from logging import getLogger

from runner.sandbox.sandbox import IsolateSandbox, SandboxBase
from django.conf import settings

RUNNER_SUPPORTED_LANGUAGES = ["c++"]

logger = getLogger(__name__)


def create_sandbox() -> IsolateSandbox:
    try:
        sandbox = IsolateSandbox()
        logger.debug("Created sandbox in {sandbox_path}".format(sandbox_path=sandbox.outer_temp_dir))
        return sandbox
    except (IOError, OSError):
        msg = "Couldn't create Sandbox"
        logger.exception(msg)
        raise Exception(msg)


def delete_sandbox(sandbox: IsolateSandbox):
    try:
        if not settings.SANDBOX_KEEP:
            sandbox.delete()
    except (IOError, OSError):
        msg = "Couldn't delete Sandbox"
        logger.exception(msg)
        raise Exception(msg)


def get_sandbox_execution_data_as_dict(sandbox):
    return {
        "execution_time": sandbox.get_execution_time(),
        "execution_wall_clock_time": sandbox.get_execution_wall_clock_time(),
        "execution_memory": sandbox.get_memory_used(),
        "exit_status": sandbox.get_exit_status(),
        "exit_code": sandbox.get_exit_code(),
    }


def get_exit_status_human_translation(exit_status):
    if exit_status == SandboxBase.EXIT_TIMEOUT:
        return "Time Limit Exceeded"

    # Wall clock timeout: returning the error to the user.
    elif exit_status == SandboxBase.EXIT_TIMEOUT_WALL:
        return "Timed out (wall clock limit exceeded)"

    # Suicide with signal (memory limit, segfault, abort): returning
    # the error to the user.
    elif exit_status == SandboxBase.EXIT_SIGNAL:
        return "Killed"

    # Sandbox error: this isn't a user error, the administrator needs
    # to check the environment.
    elif exit_status == SandboxBase.EXIT_SANDBOX_ERROR:
        return "Sandbox Error. Infrom the admin."

    # Forbidden syscall: returning the error to the user. Note: this
    # can be triggered also while allocating too much memory
    # dynamically (offensive syscall is mprotect).
    elif exit_status == SandboxBase.EXIT_SYSCALL:
        return "Killed because of forbidden syscall"

    # Forbidden file access: returning the error to the user, without
    # disclosing the offending file (can't we?).
    elif exit_status == SandboxBase.EXIT_FILE_ACCESS:
        return "Killed because of forbidden file access"

    # The exit code was nonzero: returning the error to the user.
    elif exit_status == SandboxBase.EXIT_NONZERO_RETURN:
        return "Failed because the return code was nonzero."

    elif exit_status == SandboxBase.EXIT_OK:
        return "OK"

    else:
        logger.error("Should not reach here")
        return None


def execution_successful(sandbox):
    exit_status = sandbox.get_exit_status()

    # Timeout: returning the error to the user.
    if exit_status == SandboxBase.EXIT_TIMEOUT:
        logger.debug("Execution timed out.")
        return False

    # Wall clock timeout: returning the error to the user.
    elif exit_status == SandboxBase.EXIT_TIMEOUT_WALL:
        logger.debug("Execution timed out (wall clock limit exceeded).")
        return False

    # Suicide with signal (memory limit, segfault, abort): returning
    # the error to the user.
    elif exit_status == SandboxBase.EXIT_SIGNAL:
        signal = sandbox.get_killing_signal()
        logger.debug("Execution killed with signal %d.", signal)
        return False

    # Sandbox error: this isn't a user error, the administrator needs
    # to check the environment.
    elif exit_status == SandboxBase.EXIT_SANDBOX_ERROR:
        logger.error("Evaluation aborted because of sandbox error.")
        return False

    # Forbidden syscall: returning the error to the user. Note: this
    # can be triggered also while allocating too much memory
    # dynamically (offensive syscall is mprotect).
    elif exit_status == SandboxBase.EXIT_SYSCALL:
        syscall = sandbox.get_killing_syscall()
        logger.debug("Execution killed because of forbidden "
                     "syscall: `%s'.", syscall)
        return False

    # Forbidden file access: returning the error to the user, without
    # disclosing the offending file (can't we?).
    elif exit_status == SandboxBase.EXIT_FILE_ACCESS:
        filename = sandbox.get_forbidden_file_error()
        logger.debug("Execution killed because of forbidden "
                     "file access: `%s'.", filename)
        return False

    # The exit code was nonzero: returning the error to the user.
    elif exit_status == SandboxBase.EXIT_NONZERO_RETURN:
        logger.debug("Execution failed because the return code was nonzero.")
        return False

    elif exit_status == SandboxBase.EXIT_OK:
        return True

    else:
        logger.error("Should not reach here")
        return False