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

    if time_limit:
        sandbox.timeout = time_limit
        sandbox.wallclock_timeout = 2 * time_limit + 1
    else:
        time_limit = 0

    if memory_limit:
        sandbox.address_space = memory_limit * 1024
    else:
        sandbox.address_space = 0

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

    stdouts = []
    stderrs = []

    sandbox.allow_writing_all()
    idx = 0
    for command in commands:
        execution_result = execute_command(sandbox, command, time_limit, memory_limit,
                                           stdout_redirect="stdout_{}.txt".format(idx),
                                           stderr_redirect="stderr_{}.txt".format(idx))
        stdout = str(sandbox.get_file_to_string(sandbox.stdout_file),
                     "utf-8", errors="replace").strip()
        stderr = str(sandbox.get_file_to_string(sandbox.stderr_file),
                     "utf-8", errors="replace").strip()

        stdouts.append(stdout)
        stderrs.append(stderr)
        if not execution_result:
            return False, stdouts, stderrs
        idx += 1
    return True, stdouts, stderrs


def retrieve_files(sandbox, files):
    retrieved_files = {}
    for file in files:
        try:
            stored_file = sandbox.get_file_to_storage(file)
            retrieved_files[file] = stored_file
        except IOError as e:
            logger.debug(
                "The following problem occurred when retrieving file {}: \n {}".format(
                    file, repr(e))
            )
            retrieved_files[file] = None
    return retrieved_files