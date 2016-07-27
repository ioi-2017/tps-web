from cps.local_settings import DEFAULT_TIME_LIMIT, DEFAULT_MEMORY_LIMIT
from runner.Runnable import Runnable


class Job(Runnable):
    def __init__(self, commands=None, files=None, executable_filenames=None, output_filename=None,
                 time_limit=DEFAULT_TIME_LIMIT, memory_limit=DEFAULT_MEMORY_LIMIT):
        """
        A job to be executed
        :param commands: List[List[string]], list of command lines to be executed
            every command line list of string (e.g. ["./a.out", "<a.in", ">a.out"])
        :param files: List[file_repository.File], a list files to be put in Sandbox (input files and executables)
        :param executable_filenames: List[string], files that can be executed in Sandbox
        :param output_filename: output file name to be extracted from sandbox
        :param time_limit: float, time_limit in seconds
        :param memory_limit: memory limit in bytes

        output_file: output file (Django File) generated in sandbox
        stdout: stdout of executed command by runner
        stderr: stderr of executed command by runner
        execution_time: time of executed command by runner
        execution_memory: memory of executed command by runner
        exit_code: exit code of command executed by runner
        """
        super(Job, self).__init__()

        self.commands = commands
        self.files = files
        self.executable_filenames = executable_filenames
        self.output_filename = output_filename
        self.time_limit = time_limit
        self.memory_limit = memory_limit

        # This Fields will be generated after Job is executed (run)
        self.output_file = None
        self.stdout = None
        self.stderr = None
        self.execution_time = None
        self.execution_memory = None
        self.exit_code = None

    def execute(self):
        """
        execute the job.
        if output_filename is not None:
            output File is generated and put in job.output_file
        commands can not be None before execution
        """
        raise NotImplementedError("This must be implemented in subclass")





