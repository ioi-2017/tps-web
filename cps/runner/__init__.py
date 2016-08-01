from logging import getLogger

RUNNER_SUPPORTED_LANGUAGES = []

logger = getLogger(__name__)

EXIT_SANDBOX_ERROR = 'sandbox error'
EXIT_OK = 'ok'
EXIT_SIGNAL = 'signal'
EXIT_TIMEOUT = 'timeout'
EXIT_TIMEOUT_WALL = 'wall timeout'
EXIT_FILE_ACCESS = 'file access'
EXIT_SYSCALL = 'syscall'
EXIT_NONZERO_RETURN = 'nonzero return'


def get_compilation_command(language, source_filenames, executable_filename):
    """
    returns a command to be executed by runner
    :param language: RUNNER_SUPPORTED_LANGUAGES
    :param source_filenames: string
    :param executable_filename: string
    """
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        logger.error("Language" + language + "not supported in runner")

    if language is "c++":
        command_list = ["g++", source_filenames, "-O2", "-o", executable_filename]
        return command_list


def get_execution_command(language, executable_filename):
    """
    :param language: RUNNER_SUPPORTED_LANGUAGES
    :param executable_filename: string
    :return: a command to be executed by runner
    """
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        logger.error("Language" + language + "not supported in runner")