from logging import getLogger

RUNNER_SUPPORTED_LANGUAGES = []

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
