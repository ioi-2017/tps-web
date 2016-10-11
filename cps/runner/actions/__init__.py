import logging

logger = logging.getLogger(__name__)


def execute_command(sandbox, command,
                    time_limit, memory_limit,
                    stdin_redirect=None,
                    stdout_redirect=None,
                    stderr_redirect=None):

    """ Execute some command in the sandbox

    :param sandbox (Sandbox): the sandbox used for execution
    :param command ([string]): the command to be executed
    :param time_limit (float): time limit in seconds
    :param memory_limit (int): memory limit in MB
    :return bool: True if execution was successful; False otherwise.
    """

    logger.debug("Initializing sandbox for executing {command}".format(command=command))

    sandbox.timeout = time_limit
    sandbox.wallclock_timeout = 2 * time_limit + 1

    sandbox.address_space = memory_limit * 1024

    sandbox.stdin_file = stdin_redirect

    if stdout_redirect is None:
        stdout_redirect = "stdout.txt"
    sandbox.stdout_file = stdout_redirect

    if stderr_redirect is None:
        stderr_redirect = "stderr.txt"
    sandbox.stderr_file = stderr_redirect

    sandbox.allow_writing([sandbox.stdout_file, sandbox.stderr_file])

    logger.debug("Starting execution of {command}".format(command=command))

    return sandbox.execute_without_std(command, wait=True)


def run_compilation_commands(sandbox, commands,
                            time_limit, memory_limit):
    sandbox.dirs += [("/etc", None, None)]
    sandbox.preserve_env = True
    sandbox.max_processes = None

    sandbox.allow_writing_all()
    idx = 0
    for command in commands:
        if not execute_command(sandbox, command, time_limit, memory_limit,
                               stdout_redirect="stdout_{}.txt".format(idx),
                               stderr_redirect="stderr_{}.txt".format(idx)):
            return False
        idx += 1
    return True
