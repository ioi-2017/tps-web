from logging import getLogger
import os

RUNNER_SUPPORTED_LANGUAGES = ["c++", "java", "pas"]


class NotSupportedLanguage(Exception):
    pass

logger = getLogger(__name__)


def detect_language(filename):
    extensions = {'.cpp': 'c++',
                  '.cc': 'c++',
                  '.cxx': 'c++',
                  '.c++': 'c++',
                  '.C': 'c++',
                  '.java': 'java',
                  '.pas': 'pas'}

    name, ext = os.path.splitext(filename)
    if ext not in extensions:
        return None
    return extensions[ext]


def get_valid_extensions(language):

    if language not in RUNNER_SUPPORTED_LANGUAGES:
        raise NotSupportedLanguage
    if language == "c++":
        return [".h", ".cpp"]
    elif language == "java":
        return [".java"]
    elif language == "pas":
        return [".pas"]


def get_compilation_commands(language, source_filenames, executable_filename):
    """
    returns a command to be executed by runner
    :param language: RUNNER_SUPPORTED_LANGUAGES
    :param source_filenames: list of strings
    :param executable_filename: string
    """
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        raise NotSupportedLanguage
    command_list = []
    if language == "c++":
        command_list.append(
            ["/usr/bin/g++",  "-x", "c++", "--std", "gnu++14"] + source_filenames + ["-O2", "-o", executable_filename]
        )
    elif language == "java":
        compile_command = ["/usr/bin/javac"] + source_filenames
        jar_command = ["/bin/bash", "-c",
                       " ".join([
                           "/usr/bin/jar", "cf",
                           "%s.jar" % executable_filename,
                           "*.class"])]
        mv_command = ["/bin/mv",
                      "%s.jar" % executable_filename,
                      executable_filename]
        command_list = [compile_command, jar_command, mv_command]
    elif language == "pas":
        command = ["/usr/bin/fpc"]
        command += ["-XS", "-O2", "-o%s" % executable_filename]
        command += [source_filenames[0]]
        command_list = [command]
    return command_list


def get_execution_command(language, executable_filename, main=None):
    """
    :param language: RUNNER_SUPPORTED_LANGUAGES
    :param executable_filename: string
    :param main: string; name of the class containing main function. Required for java.
    :return: a command to be executed by runner
    """
    if language not in RUNNER_SUPPORTED_LANGUAGES:
        logger.error("Language" + language + "not supported in runner")
    if main is None:
        main = executable_filename
    if language == "c++":
        import os
        command_list = [os.path.join(".", executable_filename)]
        return command_list
    elif language == "java":
        return ["/usr/bin/java", "-Xmx512M", "-Xss64M", "-cp",
                 executable_filename, main]
    elif language == "pas":
        import os
        command_list = [os.path.join(".", executable_filename)]
        return command_list


