from judge import Judge
from judge.results import JudgeVerdict
from runner.sandbox.sandbox import SandboxBase
from .batch import Batch
from runner import RUNNER_SUPPORTED_LANGUAGES


class Runner(Judge):

    def __init__(self, compile_time_limit, compile_memory_limit):
        self.compile_time_limit = compile_time_limit
        self.compile_memory_limit = compile_memory_limit
        self.task_types = {
            "Batch": Batch
        }

    def get_supported_languages(self):
        return RUNNER_SUPPORTED_LANGUAGES

    def get_score_types(self):
        pass

    def get_task_type(self, name, fallback_to_default=True):
        if name not in self.task_types:
            if not fallback_to_default:
                return None
            task_type = self.task_types["Batch"]
        else:
            task_type = self.task_types[name]
        return task_type(self)

    def get_task_types(self):
        return [x for x in self.task_types]

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