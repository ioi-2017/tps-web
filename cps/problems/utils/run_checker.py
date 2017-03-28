from runner import get_execution_command
from runner.actions.action import ActionDescription
from django.conf import settings

from runner.actions.execute_with_input import execute_with_input


def run_checker(source_file, input_file, jury_output, contestant_output):
    """
    Runs compiled executable of checker source file with the parameters:
    checker <testcase_input> <testcase_output> <contestant_output>
    The checker should output the score to standard output.
    The first line of standard error stream is the message shown to the contestant.
    """

    CHECKER_FILENAME = "checker"
    TESTCASE_INPUT_FILENAME = "input.txt"
    TESTCASE_OUTPUT_FILENAME = "jury.txt"
    CONTESTANT_OUTPUT_FILENAME = "contestant.txt"
    STDOUT_FILENAME = "stdout.txt"
    STDERR_FILENAME = "stderr.txt"

    compiled_checker = source_file.compiled_file()
    if compiled_checker is None:
        return False, None, None, None, None, None

    execution_command = get_execution_command(source_file.source_language, CHECKER_FILENAME)
    execution_command.extend([TESTCASE_INPUT_FILENAME, TESTCASE_OUTPUT_FILENAME, CONTESTANT_OUTPUT_FILENAME])
    action = ActionDescription(
        commands=[execution_command],
        executables=[(CHECKER_FILENAME, compiled_checker)],
        files=[
            (TESTCASE_INPUT_FILENAME, input_file),
            (TESTCASE_OUTPUT_FILENAME, jury_output),
            (CONTESTANT_OUTPUT_FILENAME, contestant_output)
        ],
        stdout_redirect=STDOUT_FILENAME,
        stderr_redirect=STDERR_FILENAME,
        output_files=[STDOUT_FILENAME, STDERR_FILENAME],
        time_limit=getattr(settings, "FAILSAFE_TIME_LIMIT", None),
        memory_limit=getattr(settings, "FAILSAFE_MEMORY_LIMIT", None)
    )
    success, execution_success, output_files, sandbox_datas = execute_with_input(action)

    if success and execution_success:
        stdout_file = output_files[STDOUT_FILENAME]
        stderr_file = output_files[STDERR_FILENAME]
        try:
            score = float(stdout_file.file.readline().strip())
        except ValueError:
            message = "First line of output must contain a single number, the score."
            return False, None, None, stdout_file, stderr_file, message
        if 0 <= score <= 1:
            message = "Scored successfully."
            contestant_comment = str(output_files[STDERR_FILENAME].file.readline())
            return True, score, contestant_comment, stdout_file, stderr_file, message
        else:
            message = "Score must be between 0 and 1."
            return False, None, None, stdout_file, stderr_file, message
    else:
        return False, None, None, None, None, None
