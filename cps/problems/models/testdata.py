# Amir Keivan Mohtashami

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from file_repository.models import FileModel
from problems.models import SourceFile
from problems.models.problem import ProblemRevision
from runner import get_execution_command
from runner.Job import Job
from version_control.models import VersionModel


class TestCase(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=20, verbose_name=_("name"))

    _input_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("input uploaded file"), null=True,
                                             related_name='+')
    _input_generation_parameters = models.TextField(
        verbose_name=_("input generation command"),
        max_length=1,
        null=True,
        blank=True
    )
    _input_generator = models.ForeignKey(SourceFile, verbose_name=_("generator"), null=True, related_name='+')
    _input_static = models.BooleanField(
        editable=False,
    )
    _input_file = models.ForeignKey(FileModel, editable=False, related_name='+')

    _output_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("output file"), null=True, related_name='+')
    _output_static = models.BooleanField(
        editable=False,
    )
    _output_file = models.ForeignKey(FileModel, editable=False, related_name='+')
    _solution = models.ForeignKey(SourceFile, verbose_name=_("solution"), null=True, related_name='+')

    def clean(self):
        if self._input_uploaded_file is None and self._input_generation_command is None:
            raise ValidationError("Either a file or a way to generate it must be set")

    def save(self, *args, **kwargs):
        """
        We first determine whether input and output is a static file and then continue saving process normally.
        """
        if self._input_uploaded_file is not None:
            self._input_generation_command = None
            self._input_static = True
        elif self._input_generation_command is not None:
            self._input_static = False
        else:
            # Since a model must be cleaned before saving and this is checked in the validation method,
            # we can either do nothing here or raise an error as a fail-safe.
            raise ValidationError("Validate the model before saving it")

        if self._output_uploaded_file is not None:
            self._output_static = True
        else:
            self._output_static = False

        super(TestCase, self).save(*args, **kwargs)

    def _generate_input_file(self):
        """
        In case the input is not static, generates the input using the generation command
        """

        class InputGenerationJob(Job):
            def __init__(self, test_case):
                self.test_case = test_case
                generation_command = get_execution_command(self.test_case._input_generator.source_language,
                                                           self.test_case._input_generator.compiled_file().name)

                generation_command.extend([self.test_case._input_generation_parameters])
                generation_executable_files = [
                    (self.test_case._input_generator.compiled_file(),
                     self.test_case._input_generator.compiled_file().name)]
                generation_files_to_extract = ["output.txt"]
                generation_stdout_filename = "output.txt"
                super(InputGenerationJob, self).__init__(command=generation_command,
                                                         executable_files=generation_executable_files,
                                                         stdout_filename=generation_stdout_filename,
                                                         files_to_extract=generation_files_to_extract)

            def execute(self):
                super(InputGenerationJob, self).execute()
                self.test_case._input_file = self.extracted_files["output.txt"]
                self.test_case.save()

        if self._input_static is False:
            if self._input_generator is None:
                raise AssertionError("static input dose not have generator")
            else:
                input_generation_job = InputGenerationJob(test_case=self)
                input_generation_job.run()
        else:
            raise AssertionError("can't generate input for static input")

    def generate_input_file(self):
        """
        This method is used to request generation of input file.
        As the generation process is done asynchronously it is only responsible to add the generation task
         (self._generate_input_file) to workers queue
        """
        self._generate_input_file()

    @property
    def input_file(self):
        """
        returns a File instance of the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """
        if self._input_static is False:
            if self._input_file is not None:
                return self._input_file
            else:
                self.generate_input_file()
        else:
            return self._input_uploaded_file

    def _generate_output_file(self):
        """
        In case the output is not static, generates the output using the generation command
        """

        class OutputGenerationJob(Job):
            def __init__(self, test_case):
                self.test_case = test_case
                input_file_for_generating_output = self.test_case.input_file
                generation_command = get_execution_command(self.test_case._solution.source_language,
                                                           self.test_case._solution.compiled_file().name)
                generation_input_files = [(input_file_for_generating_output, input_file_for_generating_output.name)]
                generation_executable_files = [
                    (self.test_case._solution.compiled_file(), self.test_case._solution.compiled_file().name)]
                generation_files_to_extract = ["output.txt"]
                generation_stdout_filename = "output.txt"
                generation_stdin_filename = input_file_for_generating_output.name
                generation_time_limit = self.test_case.problem.problemdata.time_limit
                generation_memory_limit = self.test_case.problem.problemdata.memory_limit
                super(OutputGenerationJob, self).__init__(command=generation_command,
                                                          input_files=generation_input_files,
                                                          executable_files=generation_executable_files,
                                                          stdin_filename=generation_stdin_filename,
                                                          stdout_filename=generation_stdout_filename,
                                                          files_to_extract=generation_files_to_extract,
                                                          time_limit=generation_time_limit,
                                                          memory_limit=generation_memory_limit)

            def execute(self):
                super(OutputGenerationJob, self).execute()
                self.test_case._output_file = self.extracted_files["output.txt"]
                self.test_case.save()

        if self._output_static is False:
            if self._solution is None:
                raise AssertionError("test case does not have solution")
            else:
                output_generation_job = OutputGenerationJob(test_case=self)
                output_generation_job.run()
        else:
            raise AssertionError("can't generate output for static output")

    def generate_output_file(self):
        """
        This method is used to request generation of output file.
        As the generation process is done asynchronously it is only responsible to add the generation task
         (self._generate_output_file) to workers queue
        """
        self._generate_output_file()

    @property
    def output_file(self):
        """
        returns a File instance for the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """
        if self._output_static is False:
            if self._output_file is not None:
                return self.output_file
            else:
                self.generate_output_file()
        else:
            return self._output_uploaded_file

    def output_file_generated(self):
        if self._output_static is True:
            return True
        else:
            return self._output_file is not None

    def input_file_generated(self):
        if self._input_static is True:
            return True
        else:
            return self._output_file is not None


class Subtask(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"), related_name="subtasks")
    name = models.CharField(max_length=100, verbose_name=_("name"))
    score = models.IntegerField(verbose_name=_("score"))

    testcases = models.ManyToManyField(TestCase, related_name="subtasks")
