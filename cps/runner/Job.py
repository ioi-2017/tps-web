from django.conf import settings
from runner.Runnable import Runnable


# TODO: add a feature to be able to run a single string command safely (e.g. "./a.out <a.in >a.out")
class Job(Runnable):
    def __init__(self, command=None, input_files=None, executable_files=None,
                 stdin_filename=None, stdout_filename=None, stderr_filename=None,
                 files_to_extract=None,
                 time_limit=settings.DEFAULT_TIME_LIMIT,
                 memory_limit=settings.DEFAULT_MEMORY_LIMIT,
                 description=None):
        """
        A job to be executed
        :param command: List[string], command will be executed with the remaining items being its arguments
            (e.g. ["diff", "a.cpp", "b.cpp"])
        :param input_files: List[(file_repository.File, filename)], a list of files to be put in Sandbox
            File will be put with "filename" in sandbox
            Note: every item is a tuple.
        :param executable_files: List[(file_repository.File, filename)], same as input_files but with executable permission
        :param stdin_filename: (string, None), redirect stdin of command from stdin_filename
        :param stdout_filename: (string, None), redirect stdout of command to stdout_filename
        :param stderr_filename: (string, None), redirect stderr of command to stdout_filename
        :param files_to_extract: List[string], filename to extract from sandbox

        :param time_limit: float, time_limit in seconds
        :param memory_limit: memory limit in bytes
        :param description: description of the job (for debug)

        extracted_files: Dict{filename, FileModel}, extracted files based on files_to_extract
        execution_time: time of executed command
        execution_memory: memory of executed command
        exit_status: exit status of command executed (EXIT_XXX in runner.__init__.py)
        success: (bool) whether the job succeeded.
        res_info: dict, additional results.
        """
        super(Job, self).__init__()
        self.command = command
        self.input_files = input_files
        self.executable_files = executable_files
        self.stdin_filename = stdin_filename
        self.stdout_filename = stdout_filename
        self.stderr_filename = stderr_filename
        self.files_to_extract = files_to_extract
        self.time_limit = time_limit
        self.memory_limit = memory_limit
        self.description = description

        # This Fields will be generated after Job is executed (run)
        self.extracted_files = None
        self.execution_time = None
        self.execution_memory = None
        self.exit_status = None
        self.success = None
        self.res_info = None

    def execute(self):
        """
        execute the job.
        command can not be None before execution
        """
        raise NotImplementedError("This must be implemented in subclass")





