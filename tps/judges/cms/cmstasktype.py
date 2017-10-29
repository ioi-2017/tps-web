# coding=utf-8
import os
import re

from judge.tasktype import TaskType
import json
import base64
import requests
import time
from judge.results import EvaluationResult, JudgeVerdict
from file_repository.models import FileModel
from django.core.files.base import ContentFile
import logging


logger = logging.getLogger(__name__)


def FileModel_to_base64(filemodel):
    file = filemodel.file
    file.open('rb')
    text = file.read()
    file.close()
    return base64.b64encode(text).decode('utf-8')


def get_judge_verdict_from_cms(status, compiled, output):
    if compiled != "Compilation succeeded":
        return False, JudgeVerdict.compilation_failed

    if status == "Execution timed out" or \
            status == "Execution timed out (wall clock limit exceeded)":
        return False, JudgeVerdict.time_limit_exceeded

    if output is None:
        return False, JudgeVerdict.runtime_error

    return True, JudgeVerdict.ok


def create_evaluation_result(failed=False, evalres=None, message=''):
    if failed:
        return EvaluationResult(
            success=False,
            output_file=None,
            execution_time=0,
            execution_memory=0,
            verdict=JudgeVerdict.judge_failed,
            message=message
        )

    success, verdict = \
        get_judge_verdict_from_cms(evalres['evalres'], evalres['compiled'], evalres['output'])

    output_file = None
    execution_memory = 0
    if success:
        output_body = base64.b64decode(evalres['output']).decode('utf-8')
        output_file = FileModel()
        output_file.file.save('output', ContentFile(output_body))
        output_file.save()

        execution_memory = float(evalres['memory']) / 1024 / 1024

    return EvaluationResult(
        success=success,
        output_file=output_file,
        execution_time=evalres['time'],
        execution_memory=execution_memory,
        verdict=verdict,
        message=evalres['message'],
    )


def _should_continue(evalres):
    return evalres['result'] is False or \
           not evalres['compiled'] or \
           (evalres['compiled'] == "Compilation succeeded" and evalres['evalres'] is None)


def test_connection(api_address):
    try:
        requests.get(api_address)
    except Exception:
        return False
    return True


class CMSTaskType(TaskType):

    def init_problem(
            self,
            problem_code,
            code_name,
            task_type_parameters,
            helpers,
            time_limit,
            memory_limit,
            task_type,
    ):
        """See TaskType.initialize_problem
           task_type is a string containing the name of the task type
        """
        if not test_connection(self.judge.api_address):
            return False, 'No connection to CMS'

        problem_code = str(problem_code)

        managers = dict()
        for name, filemodel in helpers:
            managers[name] = FileModel_to_base64(filemodel)
        managers_json = json.dumps(managers)

        if task_type_parameters is None or \
                task_type_parameters == '':
            task_type_parameters = '{}'
        task_type_parameters = json.loads(task_type_parameters)
        params_form_class = self.get_parameters_form()
        params_form = params_form_class(task_type_parameters)
        tt_params = params_form.to_payload()

        payload = {'name': problem_code,
                   'time_limit': time_limit,
                   'memory_limit': memory_limit,
                   'task_type': task_type,
                   'score_type': 'Sum',
                   'score_type_parameters': 100,
                   'managers': managers_json,
                   'submission_format': '["{}.%l"]'.format(code_name)}
        payload.update(tt_params)

        response = requests.post(self.judge.api_address + 'tasks/add',
                                 data=payload)
        if response.status_code != 200:
            return False, "%d Error" % response.status_code
        result = json.loads(response.text)

        if result['status'] is False and result['message'] == \
                'A problem with this name already exists':
            logger.warning('Task with this name found. Deleting it now...')
            response = requests.get(self.judge.api_address + 'task/'
                                    + problem_code + '/remove')
            if response.status_code != 200:
                return False, "%d Error while deleting" % response.status_code
            result = json.loads(response.text)
            if result['status'] is False:
                return False, result['message']

            response = requests.post(self.judge.api_address + 'tasks/add',
                                     data=payload)
            if response.status_code != 200:
                return False, "%d Error" % response.status_code
            result = json.loads(response.text)

        return result['status'], result['message']

    def add_testcase(self, problem_code, testcase_code, input_file):
        if not test_connection(self.judge.api_address):
            return False, 'No connection to CMS'

        # testcase code name should not contain sapces
        testcase_code = problem_code + '_' + testcase_code.replace(' ', '_')

        input_encoded = FileModel_to_base64(input_file)
        output_encoded = base64.b64encode(b'').decode('utf-8')
        payload = {'testcase_id': testcase_code,
                   'input': input_encoded,
                   'output': output_encoded}

        response = requests.post(self.judge.api_address + 'task/'
                                 + problem_code + '/testcases/add',
                                 data=payload)
        if response.status_code != 200:
            return False, "%d Error" % response.status_code
        result = json.loads(response.text)

        if result['status'] is False and result['message'] == \
                'A testcase with this code already exists':
            logger.warning('Testcase with this name found. Deleting it now...')
            response = requests.get(self.judge.api_address + 'task/'
                                    + problem_code + '/testcase/'
                                    + testcase_code + '/delete')
            if response.status_code != 200:
                return False, "%d Error while deleting" % response.status_code
            result = json.loads(response.text)
            if result['status'] is False:
                return False, result['message']

            response = requests.post(self.judge.api_address + 'task/'
                                     + problem_code + '/testcases/add',
                                     data=payload)
            if response.status_code != 200:
                return False, "%d Error" % response.status_code
            result = json.loads(response.text)

        return result['status'], result['message']

    def generate_output(self, problem_code, testcase_code, language,
                        solution_file):
        if language is None:
            language = self.judge.detect_language(solution_file[0])

        if language == 'text':
            return EvaluationResult(
                success=True,
                output_file=solution_file[1],
                execution_time=0,
                execution_memory=0,
                verdict=JudgeVerdict.ok,
                message='The output is the input!',
            )

        if not test_connection(self.judge.api_address):
            return create_evaluation_result(failed=True,
                                            message='No connection to CMS')

        # testcase code name should not contain sapces
        testcase_code = problem_code + '_' + testcase_code.replace(' ', '_')

        files = dict()
        files['{}.%l'.format(os.path.splitext(solution_file[0])[0])] = FileModel_to_base64(solution_file[1])
        files_json = json.dumps(files)

        payload = {'files': files_json,
                   'language': language}
        response = requests.post(self.judge.api_address + 'task/'
                                 + problem_code + '/testcase/'
                                 + testcase_code + '/run', data=payload)
        if response.status_code != 200:
            return create_evaluation_result(failed=True,
                                            message='%d Error' % response.status_code)
        result = json.loads(response.text)
        if result['status'] is False:
            return create_evaluation_result(failed=True, message=result['message'])
        else:
            submission_id = str(result['message'])

        while True:
            time.sleep(5)
            response = requests.get(self.judge.api_address + 'task/'
                                    + problem_code + '/test/' + submission_id
                                    + '/result')
            if response.status_code != 200:
                return create_evaluation_result(failed=True,
                                                message='%d Error' % response.status_code)
            result = json.loads(response.text)
            if not result['status']:
                return create_evaluation_result(failed=True, message=result['message'])
            evalres = json.loads(result['message'])
            if _should_continue(evalres):
                continue
            break

        return create_evaluation_result(evalres=evalres)
