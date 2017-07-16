from enum import Enum
from urllib.parse import _noop


class SolutionVerdict(Enum):
    model_solution = (_noop("Model solution"), "AC")
    correct = (_noop("Correct"), "AC")
    time_limit = (_noop("Time limit"), "TL")
    memory_limit = (_noop("Memory limit"), "ML")
    incorrect = (_noop("Incorrect"), "WA")
    runtime_error = (_noop("Runtime error"), "RE")
    failed = (_noop("Failed"), "FL")
    time_limit_and_runtime_error = (_noop("Time limit / Runtime error"), "TL/RE")
    partially_correct = (_noop("Partial Score"), "PS")

    def __init__(self, full_name, short_name):
        self.full_name = full_name
        self.short_name = short_name

    def __str__(self):
        return self.full_name


class SolutionRunVerdict(Enum):
    judging = (_noop("Judging"), "N / A")
    invalid_submission = (_noop("Invalid Submission"), "BS")
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

    @classmethod
    def get_from_judge_verdict(cls, verdict):
        # FIXME: The following line makes the implicit requirement that all members of JudgeVerdict
        # will be present in SolutionRunVerdict. Either remove this requirement or make it explicit.
        return cls.__members__.get(verdict.name)
