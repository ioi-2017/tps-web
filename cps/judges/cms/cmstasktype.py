# coding=utf-8

from judge.tasktype import TaskType
import json
import base64
import requests
import time
from django.conf import settings
from judge.results import EvaluationResult, JudgeVerdict
from file_repository.models import FileModel
from django.core.files.base import ContentFile
import logging


logger = logging.getLogger(__name__)


def FileModel_to_base64(filemodel):
    file = filemodel.file
    file.open('rb')
    lines = file.readlines()
    file.close()
    text = b""
    for line in lines:
        text += line
    return base64.b64encode(text).decode('utf-8')


def get_judge_verdict_from_cms(status, compiled):
    if compiled == '["Compilation failed"]':
        return False, JudgeVerdict.compilation_failed
    if status == '["Execution completed successfully"]':
        return True, JudgeVerdict.ok
    if status == '["Execution timed out"]':
        return False, JudgeVerdict.time_limit_exceeded
    # FIXME: not so specific
    return False, JudgeVerdict.runtime_error


def create_evaluation_result(problem_code='', submission_id='', failed=False, evalres=None, message=''):
    if failed:
        return EvaluationResult(
            success=False,
            output_file=None,
            execution_time=0,
            execution_memory=0,
            verdict=JudgeVerdict.judge_failed,
            message=message
        )

    success, verdict = get_judge_verdict_from_cms(evalres['evalres'], evalres['compiled'])

    output_file = None
    if success:
        response = requests.get(settings.CMS_API_ADDRESS + 'task/'
                                + problem_code + '/test/' + submission_id
                                + '/output')
        if response.status_code != 200:
            return create_evaluation_result(failed=True,
                                            message='%d Error' % response.status_code)
        result = json.loads(response.text)
        output_body = base64.b64decode(result['message']).decode('utf-8')

        output_file = FileModel()
        output_file.file.save('output_' + problem_code + '_' + submission_id,
                              ContentFile(output_body))
        output_file.save()

    execution_memory = float(evalres['memory']) / 1024 / 1024

    return EvaluationResult(
        success=success,
        output_file=output_file,
        execution_time=evalres['time'],
        execution_memory=execution_memory,
        verdict=verdict,
        message=evalres['evalres'],
    )


def _should_continue(evalres):
    if evalres['evalres'] is None:
        return True
    return False


class CMSTaskType(TaskType):

    def init_problem(
            self,
            problem_code,
            task_type_parameters,
            helpers,
            time_limit,
            memory_limit,
            task_type,
    ):
        """See TaskType.initialize_problem
           task_type is a string containing the name of the task type
        """
        def send_request():
            response = requests.post(settings.CMS_API_ADDRESS + 'tasks/add',
                                     data=payload)
            if response.status_code != 200:
                return False, "%d Error" % response.status_code
            result = json.loads(response.text)
            return result

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
                   'submission_format': '["solution.%l"]'}
        payload.update(tt_params)

        result = send_request()

        if result['status'] is False and result['message'] == \
                'A problem with this name already exists':
            response = requests.get(settings.CMS_API_ADDRESS + 'task/'
                                    + problem_code + '/remove')
            if response.status_code != 200:
                return False, "%d Error while deleting" % response.status_code
            result = json.loads(response.text)
            if result['status'] is False:
                return False, result['message']

            result = send_request()

        return result['status'], result['message']

    def add_testcase(self, problem_code, testcase_code, input_file):
        def send_request():
            response = requests.post(settings.CMS_API_ADDRESS + 'task/'
                                     + problem_code + '/testcases/add',
                                     data=payload)
            if response.status_code != 200:
                return False, "%d Error" % response.status_code
            result = json.loads(response.text)
            return result

        # testcase code name should not contain sapces
        testcase_code = problem_code + '_' + testcase_code.replace(' ', '_')

        input_encoded = FileModel_to_base64(input_file)
        output_encoded = base64.b64encode(b'').decode('utf-8')
        payload = {'testcase_id': testcase_code,
                   'input': input_encoded,
                   'output': output_encoded}

        result = send_request()

        if result['status'] is False and result['message'] == \
                'A testcase with this code already exists':
            response = requests.get(settings.CMS_API_ADDRESS + 'task/'
                                    + problem_code + '/testcase/'
                                    + testcase_code + '/delete')
            if response.status_code != 200:
                return False, "%d Error while deleting" % response.status_code
            result = json.loads(response.text)
            if result['status'] is False:
                return False, result['message']

            result = send_request()

        return result['status'], result['message']

    def generate_output(self, problem_code, testcase_code, language,
                        solution_file):
        if language == 'text':
            return EvaluationResult(
                success=True,
                output_file=solution_file[1],
                execution_time=0,
                execution_memory=0,
                verdict=JudgeVerdict.ok,
                message='The output is the input!',
            )

        # testcase code name should not contain sapces
        testcase_code = problem_code + '_' + testcase_code.replace(' ', '_')

        files = dict()
        files['solution.%l'] = FileModel_to_base64(solution_file[1])
        files_json = json.dumps(files)

        payload = {'files': files_json,
                   'language': language}
        response = requests.post(settings.CMS_API_ADDRESS + 'task/'
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

        evalres = None
        while True:
            time.sleep(5)
            response = requests.get(settings.CMS_API_ADDRESS + 'task/'
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

        if evalres is None:
            return create_evaluation_result(failed=True,
                                            message='No evaluation result for submission %s' % submission_id)
        return create_evaluation_result(problem_code=problem_code,
                                        submission_id=submission_id,
                                        evalres=evalres)
