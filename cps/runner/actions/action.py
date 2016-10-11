class ActionDescription(object):

    def __init__(
        self,
        commands,
        time_limit,
        memory_limit,
        files=None,
        executables=None,
        output_files=None,
        stdin_redirect=None,
        stdout_redirect=None,
        stderr_redirect=None
    ):
        self.commands = commands

        if files:
            self.files = files
        else:
            self.files = []

        if executables:
            self.executables = executables
        else:
            self.executables = []

        if output_files:
            self.output_files = output_files
        else:
            self.output_files = []

        self.time_limit = time_limit
        self.memory_limit = memory_limit

        self.stdin_redirect = stdin_redirect
        self.stdout_redirect = stdout_redirect
        self.stderr_redirect = stderr_redirect


