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