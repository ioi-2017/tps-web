from logging import getLogger

from runner.sandbox.sandbox import IsolateSandbox

RUNNER_SUPPORTED_LANGUAGES = ["c++"]

logger = getLogger(__name__)


def get_compilation_command(language, source_filenames, executable_filename):
    """
    returns a command to be executed by runner
    :param language: RUNNER_SUPPORTED_LANGUAGES
    :param source_filenames: string
    :param executable_filename: string
    """
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        logger.error("Language" + language + "not supported in runner")

    if language == "c++":
        command_list = ["/usr/bin/g++", source_filenames, "-O2", "-o", executable_filename]
        return command_list


def get_execution_command(language, executable_filename):
    """
    :param language: RUNNER_SUPPORTED_LANGUAGES
    :param executable_filename: string
    :return: a command to be executed by runner
    """
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        logger.error("Language" + language + "not supported in runner")

    if language == "c++":
        import os
        command_list = [os.path.join(".", executable_filename)]
        return command_list


def get_source_file_name(language):
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        logger.error("Language" + language + "not supported in runner")

    if language == "c++":
        return "code.cpp"


def create_sandbox() -> IsolateSandbox:
    try:
        sandbox = IsolateSandbox()
        return sandbox
    except (IOError, OSError):
        msg = "Couldn't create Sandbox"
        logger.exception(msg)
        raise AssertionError(msg)


def delete_sandbox(sandbox: IsolateSandbox):
    try:
        sandbox.delete()
    except (IOError, OSError):
        msg = "Couldn't delete Sandbox"
        logger.exception(msg)
        raise AssertionError(msg)
