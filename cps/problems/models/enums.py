from enum import Enum
from urllib.parse import _noop


class SolutionVerdict(Enum):
    model_solution = _noop("Model solution")
    correct = _noop("Correct")
    time_limit = _noop("Time limit")
    memory_limit = _noop("Memory limit")
    incorrect = _noop("Incorrect")
    runtime_error = _noop("Runtime error")
    failed = _noop("Failed")
    time_limit_and_runtime_error = _noop("Time limit / Runtime error")


class SolutionRunVerdict(Enum):
    invalid_submission = (_noop("Bad Submission"), "BS")
    compilation_failed = (_noop("Compilation Error"), "CE")
    runtime_error = (_noop("Runtime error"), "RE")
    time_limit_exceeded = (_noop("Time limit exceeded"), "TLE")
    memory_limit_exceeded = (_noop("Memory limit exceeded"), "MLE")
    ok = (_noop("OK"), "OK")
    checker_failed = (_noop("Checker failed"), "CHKFL")
    invalid_testcase = (_noop("Invalid testcase"), "INVLDTC")
    judge_failed = (_noop("Judge failed"), "JUDFL")

    def __init__(self, full_name, short_name):
        self.full_name = full_name
        self.short_name = short_name


