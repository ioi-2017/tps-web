from logging import getLogger

from runner.sandbox.sandbox import IsolateSandbox
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