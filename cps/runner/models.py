import logging

from django.conf import settings
from django.core.files.base import File
from django.db import models

from file_repository.models import FileModel
from runner.runnable import Runnable

from runner.sandbox.sandbox import IsolateSandbox

logger = logging.getLogger(__name__)


# TODO: add a feature to be able to run a single string command safely (e.g. "./a.out <a.in >a.out")
class JobFile(models.Model):
    """
        every file of a job (input files and extracted files) will be put in this model
        input_file: (READ, WRITE, EXECUTABLE), file will be put in sandbox with name "filename"
        exracted_file: (EXTRACTED), file with name "filename" will be extraced from sandbox
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
    """a file with write access to be put in Sandbox"""
    EXTRACTED = 'extract'
    """a file extracted from sandbox"""
    type = models.CharField(max_length=20, blank=False,
                            choices=(
                                (EXECUTABLE, 'executable'),
                                (READONLY, 'read'),
                                (WRITABLE, 'write'),
                                (EXTRACTED, 'extracted'),
                            ))


class JobModel(models.Model, Runnable):
    command = models.CharField(max_length=100)
    files = models.ManyToManyField(FileModel, through="JobFile")

    stdin_filename = models.CharField(max_length=100, blank=True)
    stdout_filename = models.CharField(max_length=100, blank=True)
    stderr_filename = models.CharField(max_length=100, blank=True)

    # files_to_extract =
    time_limit = models.FloatField(default=settings.DEFAULT_TIME_LIMIT)
    memory_limit = models.IntegerField(default=settings.DEFAULT_MEMORY_LIMIT)

    description = models.CharField(max_length=20, blank=True, null=True)

    # results
    # maybe add another Model like JobResult for results? (so we dont have null at the beginning)

    execution_time = models.FloatField(null=True, blank=True)
    execution_memory = models.IntegerField(null=True, blank=True)

    success = models.NullBooleanField(blank=True)
    exit_status = models.CharField(max_length=20, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

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

    exit_status: exit status of executed command (EXIT_XXX in runner.__init__.py)
    exit_code: exit code of executed command
    if success is False then
        exit_status == ""
        exit_code is None
    """

    def add_file(self, file_model: FileModel, filename: str, type: str):
        """
        add file to job
        :param type: must be one of the choices specified in JobFile
        """
        if type not in [JobFile.READONLY, JobFile.WRITABLE, JobFile.EXECUTABLE]:
            raise AssertionError("file type is not valid")
        JobFile(job_model=self, file_model=file_model, filename=filename, type=type).save()

    def mark_file_for_extraction(self, filename: str) -> JobFile:
        """
        add a filename to extract from sandbox
        :return: the JobFile created
        """
        jf = JobFile(job_model=self, file_model=None, filename=filename, type=JobFile.EXTRACTED)
        jf.save()
        return jf

    def execute(self):
        """
        execute the job.
        command can not be None before execution
        """
        try:
            sandbox = IsolateSandbox()
        except (IOError, OSError):
            msg = "Couldn't create Sandbox"
            logger.exception(msg)
            raise JobException(msg)

        try:

            #   compilation: this were in cms compilation funciton
            #    sandbox.dirs += [("/etc", None, None)]
            #    sandbox.preserve_env = True

            sandbox.timeout = self.time_limit
            sandbox.wallclock_timeout = 2 * self.time_limit + 1

            sandbox.address_space = self.memory_limit

            sandbox.stdin_file = self.stdin_filename
            sandbox.stdout_file = self.stdout_filename
            sandbox.stderr_file = self.stderr_filename

            if sandbox.stdout_file == "":
                sandbox.stdout_file = "stdout.txt"
            if sandbox.stderr_file == "":
                sandbox.stderr_file = "stderr.txt"

            sandbox.allow_writing_only([sandbox.stdout_file, sandbox.stderr_file])

            # handle files
            for job_file in self.jobfile_set:
                file_model, filename = job_file.file_model, job_file.filename
                if job_file.type == JobFile.EXECUTABLE:
                    with file_model.file.open() as fobj:
                        sandbox.create_file_from_fileobj(filename, fobj, executable=True)
                if job_file.type in [JobFile.READONLY, JobFile.WRITABLE]:
                    with file_model.file.open() as fobj:
                        sandbox.create_file_from_fileobj(filename, fobj)
                if job_file.type == JobFile.WRITABLE:
                    sandbox.allow_writing_only([filename])
        except (IOError, OSError):
            msg = "Problem in moving necessary files to sandbox"
            logger.exception(msg)
            raise JobException(msg)

        self.success = sandbox.execute_without_std(self.command, wait=True)
        if not self.success:
            raise JobException("Job was not executed")
        try:
            for job_file in self.jobfile_set.filter(type=JobFile.EXTRACTED):
                filename = job_file.filename
                if not sandbox.file_exists(filename):
                    raise JobException("file" + filename + "does not exist")
                else:
                    with sandbox.get_file(filename) as fobj:
                        description = " ".join([str(self.id), ",", self.description])
                        info = " ".join(["Created", filename, "in job", description])
                        logger.debug(info)
                        # XXX: this will not work without a good file cacher or rsync
                        # and will most likely change in the future
                        file_model = FileModel(file=File(fobj), description=description)
                        file_model.save()
                        job_file.file_model = file_model
        except (IOError, OSError):
            msg = "Problem in extracting requested files from sandbox"
            logger.exception(msg)
            raise JobException(msg)

        self.execution_time = sandbox.get_execution_time()
        self.execution_memory = sandbox.get_memory_used()
        self.exit_status = sandbox.get_exit_status()
        self.exit_code = sandbox.get_exit_code

        if not settings.SANDBOX_KEEP:
            sandbox.delete()


class JobException(Exception):
    """Job was executed with an error"""
    pass
