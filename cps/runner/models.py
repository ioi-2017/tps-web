import json
import logging
from typing import List

from django.conf import settings
from django.core.files.base import File
from django.db import models

from file_repository.models import FileModel
from runner import create_sandbox, delete_sandbox

logger = logging.getLogger(__name__)

# TODO: add a feature to be able to run a single string command safely (e.g. "./a.out <a.in >a.out")
class JobFile(models.Model):
    """
        every file of a job (input files and extracted files) will be put in this model
        input_file: (READ, WRITE, EXECUTABLE), file will be put in sandbox with name "filename"
        extracted_file: (EXTRACTED), file with name "filename" will be extracted from sandbox
        """
    job_model = models.ForeignKey('JobModel')
    file_model = models.ForeignKey(FileModel, blank=True, null=True)
    filename = models.CharField(max_length=100)
    """
    name of file to be put in sandbox or
    name of the file extracted from sandbox
    """

    EXECUTABLE = 'exec'
    READONLY = 'r'
    """a file with read access to be put in Sandbox"""
    WRITABLE = 'w'
    """a file with write access to be put in Sandbox (it will also be readable)"""
    EXTRACTED = 'extract'
    """a file extracted from sandbox"""
    type = models.CharField(max_length=20, blank=False,
                            choices=(
                                (EXECUTABLE, 'executable'),
                                (READONLY, 'read'),
                                (WRITABLE, 'write'),
                                (EXTRACTED, 'extracted'),
                            ))

    class Meta:
        unique_together = ("job_model", "filename", "type")

    def __str__(self):
        return "job_model:(%s) file_model:(%s) type:(%s)" % (str(self.job_model), str(self.file_model), self.type)


class JobModel(models.Model):
    _command = models.CharField(max_length=100)
    """
    JSON field representation of List[str]
    use JobModel.command (property) instead
    """
    files = models.ManyToManyField(FileModel, through="JobFile")

    stdin_filename = models.CharField(max_length=100, blank=True)
    stdout_filename = models.CharField(max_length=100, blank=True)
    stderr_filename = models.CharField(max_length=100, blank=True)

    # files_to_extract =
    time_limit = models.FloatField(default=settings.DEFAULT_TIME_LIMIT)
    memory_limit = models.IntegerField(default=settings.DEFAULT_MEMORY_LIMIT)

    compile_job = models.BooleanField(default=False)

    description = models.CharField(max_length=20, blank=True)

    # results
    # maybe add another Model like JobResult for results? (so we dont have null at the beginning)

    execution_time = models.FloatField(null=True, blank=True)
    execution_wall_clock_time = models.FloatField(null=True, blank=True)
    execution_memory = models.IntegerField(null=True, blank=True)

    success = models.NullBooleanField(blank=True)
    exit_status = models.CharField(max_length=20, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

    # for debug, isolate_message is also within isolate_log
    isolate_log = models.CharField(max_length=100, blank=True)
    isolate_message = models.CharField(max_length=100, blank=True)

    """
    A job to be executed
    command: command will be executed with the remaining items being its arguments
        (e.g. ["diff", "a.cpp", "b.cpp"])
        has to be specified
    files: files related to this job

    stdin_filename: redirect stdin of command from stdin_filename
    stdout_filename: redirect stdout of command to stdout_filename
    stderr_filename: redirect stderr of command to stdout_filename

    time_limit: float, time_limit in seconds
    memory_limit: memory limit in KB
    description: description of the job (for debug)


    execution_time: time of executed command
    execution_memory: memory of executed command
    success: (bool) whether the command executed in sandbox or not.

    exit_status: exit status of executed command (EXIT_XXX in sandbox.SandboxBase)
    exit_code: exit code of executed command
    if success is False then
        exit_status == ""
        exit_code is None
    """

    @property
    def command(self) -> List[str]:
        cmd = json.loads(self._command)
        if not isinstance(cmd, list) or not all(isinstance(s, str) for s in cmd):
            raise TypeError(self._command + " stored in model, is not a List[str]")
        return cmd

    @command.setter
    def command(self, cmd: List[str]):
        if not isinstance(cmd, list) or not all(isinstance(s, str) for s in cmd):
            raise TypeError(cmd + " in setter, is not a List[str]")
        self._command = json.dumps(cmd)

    def add_file(self, file_model: FileModel = None, type: str = None, filename: str = None):
        """
        Add file to job

        FileModel should have been saved before calling this function.

        If file_model is None an empty file with name "filename" will be created.

        If file_name is None file_model will be saved in sandbox with name file_model.file.name

        :param filename: default is file_model.file.name
        :param type: must be one of the choices specified in JobFile
        """
        if self.pk is None:
            raise AssertionError("JobModel pk is None (maybe you haven't saved JobModel before this function)")
        if filename is None or filename == "":
            if file_model is None:
                raise AssertionError("file_model and filename can't both be None")
            filename = file_model.file.name

        if type not in [JobFile.READONLY, JobFile.WRITABLE, JobFile.EXECUTABLE]:
            raise AssertionError("file type is not valid")
        JobFile(job_model=self, file_model=file_model, filename=filename, type=type).save()

    def mark_file_for_extraction(self, filename: str) -> JobFile:
        """
        Add a filename to extract from sandbox,
        File_model will be stored in return.file_model after job.execute()

        FileModel should have been saved before calling this function
        :return: the JobFile created
        """
        if self.pk is None:
            raise AssertionError("JobModel pk is None (maybe you haven't saved JobModel before this function)")
        jf = JobFile(job_model=self, file_model=None, filename=filename, type=JobFile.EXTRACTED)
        jf.save()
        return jf

    def get_extracted_file(self, filename: str) -> FileModel:
        """
        Get file after job.execute.

        Filename must be specified with mark_file_for_extraction before job.execute
        """
        if self.pk is None:
            raise AssertionError("JobModel pk is None (maybe you haven't saved JobModel before this function)")
        # will return one file because of unique_together in JobFile
        return self.jobfile_set.get(filename=filename, type=JobFile.EXTRACTED).file_model

    def execute(self, sandbox):
        """
        Execute the job.

        Command can not be None before execution.
        """

        try:

            #   compilation: this were in cms compilation function
            if self.compile_job:
                # sandbox.dirs += [("/etc", None, None)]
                # g++ needs access to ld
                sandbox.preserve_env = True
                # g++ needs to be able to fork
                sandbox.max_processes = None

            sandbox.timeout = self.time_limit
            sandbox.wallclock_timeout = 2 * self.time_limit + 1

            sandbox.address_space = self.memory_limit

            sandbox.stdin_file = self.stdin_filename
            sandbox.stdout_file = self.stdout_filename
            sandbox.stderr_file = self.stderr_filename

            if sandbox.stdin_file == "":
                sandbox.stdin_file = None
            if sandbox.stdout_file == "":
                sandbox.stdout_file = "stdout.txt"
            if sandbox.stderr_file == "":
                sandbox.stderr_file = "stderr.txt"

            writable_files = []
            writable_files += [sandbox.stdout_file, sandbox.stderr_file]

            # handle files
            for job_file in self.jobfile_set.all():
                file_model, filename = job_file.file_model, job_file.filename
                if job_file.type == JobFile.EXECUTABLE:
                    sandbox.create_file_from_fileobj(filename, file_model.file, executable=True)
                if job_file.type == JobFile.READONLY:
                    sandbox.create_file_from_fileobj(filename, file_model.file)
                if job_file.type == JobFile.WRITABLE:
                    # if no file_model is specified create an empty file
                    if file_model is None:
                        sandbox.create_file(filename).close()
                    else:
                        sandbox.create_file_from_fileobj(filename, file_model.file)
                    writable_files += [filename]
        except (IOError, OSError):
            msg = "Problem in moving necessary files to sandbox"
            logger.exception(msg)
            raise JobException(msg)

        # only writable_files will have write permission
        # don't use sandbox.allow_writing_only twice because previous permissions will be reset
        sandbox.allow_writing(writable_files, only_these=True)
        if self.compile_job:
            sandbox.allow_writing_all(sandbox.path)

        self.success = sandbox.execute_without_std(self.command, wait=True)

        logger.debug("Isolate log:" + str(sandbox.get_log_string()))
        # message is a line in sandbox.log
        logger.debug("Isolate message:" + str(sandbox.get_message()))
        with sandbox.get_file(sandbox.stderr_file) as f:
            logger.debug("stderr: " + f.read().decode("utf-8"))

        if not self.success:
            raise JobException("Job was not executed")
        try:
            for job_file in self.jobfile_set.filter(type=JobFile.EXTRACTED):
                filename = job_file.filename
                if not sandbox.file_exists(filename):
                    raise JobException("file " + filename + " does not exist")
                else:
                    with sandbox.get_file(filename) as fobj:
                        description = " ".join([str(self.id), ",", self.description])
                        info = " ".join(["Created", filename, "in job", description])
                        logger.debug(info)
                        # XXX: this will not work without a good file cacher or rsync
                        # and will most likely change in the future

                        # TODO: is this the best efficient way to do it in django (two saves)?
                        file_model = FileModel(file=File(fobj), description=description)
                        file_model.save()
                        job_file.file_model = file_model
                        job_file.save()
        except (IOError, OSError):
            msg = "Problem in extracting requested files from sandbox"
            logger.exception(msg)
            raise JobException(msg)
        finally:
            self.execution_time = sandbox.get_execution_time()
            self.execution_wall_clock_time = sandbox.get_execution_wall_clock_time()
            self.execution_memory = sandbox.get_memory_used() / 1024  # KB
            self.exit_status = sandbox.get_exit_status()
            self.exit_code = sandbox.get_exit_code()
        self.save()

    def run(self):
        logger.debug("Creating Sandbox")
        sandbox = create_sandbox()

        logger.debug("Executing command in Sandbox")
        self.execute(sandbox)

        if not settings.SANDBOX_KEEP:
            logger.debug("Deleting Sandbox")
            delete_sandbox(sandbox)

    def __str__(self):
        return "%d,%s" % (self.id, self.command)


class JobException(Exception):
    """Job was executed with an error"""
    pass
