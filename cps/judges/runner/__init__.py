from judge import Judge
from judge.results import EvaluationResult, JudgeVerdict
from runner.sandbox.sandbox import SandboxBase
from .batch import Batch
from problems.models import ProblemRevision, TestCase
from runner import get_source_file_name, get_compilation_commands, get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.compile_source import compile_source
from runner.actions.execute_with_input import execute_with_input


class Runner(Judge):

    def __init__(self, compile_time_limit, compile_memory_limit):
        self.compile_time_limit = compile_time_limit
        self.compile_memory_limit = compile_memory_limit
        self.task_types = {
            "Batch": Batch
        }

    def initialize_problem(self, problem_id, task_type, score_type, helpers, problem_code=None):
        """
        For details about arguments refer to parent class.
        problem_id must be the revision_id of the problem
        """
        return problem_id

    def get_supported_languages(self):
        return ["c++"]

    def get_score_types(self):
        pass

    def add_testcase(self, problem_code, testcase_id, input_file, time_limit, memory_limit):
        """
        For details about arguments refer to parent class.
        uid for each testcase must be its pk.
        """
        return testcase_id

    def get_task_type(self, name):
        return self.task_types[name]

    def generate_output(self, problem_code, language, solution_files, testcase_code):

        if len(solution_files) != 1:
            raise ValueError("This judge only supports single file solutions")
        if language not in self.get_supported_languages():
            return EvaluationResult(
                success=False,
                verdict=JudgeVerdict.invalid_submission,
                message="Language not supported"
            )

        revision = ProblemRevision.objects.get(pk=problem_code)
        graders = [(grader.name, grader.code) for grader in revision.grader_set.filter(language=language)]

        name, file = solution_files[0]
        code_name = get_source_file_name(language)
        compiled_file_name = "code.out"
        compile_commands = get_compilation_commands(
            language,
            [code_name] + [name for name, file in graders],
            compiled_file_name
        )

        # TODO: Add managers for compiling
        action = ActionDescription(
            commands=compile_commands,
            files=[(code_name, file)] + graders,
            output_files=[compiled_file_name],
            time_limit=self.compile_time_limit,
            memory_limit=self.compile_memory_limit,
        )


        # TODO: When changed to test case specific limits, this must be changed
        time_limit = revision.problem_data.time_limit
        memory_limit = revision.problem_data.memory_limit
        testcase = TestCase.objects.get(pk=testcase_code)

        success, compilation_success, outputs, stdout, stderr, compilation_sandbox_data = compile_source(action)
        if not success or not compilation_success:
            compilation_message = "Compilation not successful"
            compilation_message += "Standard output:\n" + stdout
            compilation_message += "Standard error:\n" + stderr
            return EvaluationResult(
                success=False,
                message=compilation_message,
                verdict=JudgeVerdict.compilation_failed
            )

        compiled = outputs[compiled_file_name]

        execution_command = get_execution_command(language, "compiled")
        stdout_redirect = "output.txt"
        action = ActionDescription(
            commands=[execution_command],
            executables=[("compiled", compiled)],
            files=[("input.txt", testcase.input_file)],
            stdin_redirect="input.txt",
            stdout_redirect=stdout_redirect,
            output_files=[stdout_redirect],
            time_limit=time_limit,
            memory_limit=memory_limit
        )
        success, execution_success, outputs, execution_sandbox_datas = execute_with_input(action)

        if not success:
            evaluation_success = False
        else:
            evaluation_success = True

        if not execution_success:
            output_file = None
        else:
            output_file = outputs[stdout_redirect]

        return EvaluationResult(
                success=evaluation_success,
                output_file=output_file,
                execution_time=execution_sandbox_datas[0]["execution_time"],
                execution_memory=execution_sandbox_datas[0]["execution_memory"],
                verdict=self.get_verdict_from_exit_status(execution_sandbox_datas[0]["exit_status"]),
        )

    def get_score_type(self, name):
        pass

    def get_task_types(self):
        return [x for x in self.task_types]

    def get_score(self, problem_code, max_score, scores):
        pass

    @staticmethod
    def get_verdict_from_exit_status(exit_status):
        if exit_status == SandboxBase.EXIT_TIMEOUT:
            return JudgeVerdict.time_limit_exceeded
        elif exit_status == SandboxBase.EXIT_TIMEOUT_WALL:
            return JudgeVerdict.time_limit_exceeded
        elif exit_status == SandboxBase.EXIT_SIGNAL:
            return JudgeVerdict.runtime_error
        elif exit_status == SandboxBase.EXIT_SYSCALL:
            return JudgeVerdict.runtime_error
        elif exit_status == SandboxBase.EXIT_FILE_ACCESS:
            return JudgeVerdict.runtime_error
        elif exit_status == SandboxBase.EXIT_NONZERO_RETURN:
            return JudgeVerdict.runtime_error
        elif exit_status == SandboxBase.EXIT_OK:
            return JudgeVerdict.ok
        else:
            raise ValueError ("We should not reach this line")