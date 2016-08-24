# Amir Keivan Mohtashami

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from file_repository.models import FileModel
from problems.models import SourceFile, JobFile
from problems.models.problem import ProblemRevision
from problems.utils import run_with_input
from runner import get_execution_command
from runner.models import JobModel
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
    _input_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+')

    _output_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("output file"), null=True, related_name='+')
    _output_static = models.BooleanField(
        editable=False,
    )
    _output_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+')
    _solution = models.ForeignKey(SourceFile, verbose_name=_("solution"), null=True, related_name='+')

    def clean(self):
        if self._input_uploaded_file is None and self._input_generation_parameters is None:
            raise ValidationError("Either a file or a way to generate it must be set")

    def save(self, *args, **kwargs):
        """
        We first determine whether input and output is a static file and then continue saving process normally.
        """
        if self._input_uploaded_file is not None:
            self._input_generation_parameters = None
            self._input_static = True
        elif self._input_generation_parameters is not None:
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
        if self._input_static is False:
            if self._input_generator is None:
                raise AssertionError("static input dose not have generator")
            else:
                generation_command = get_execution_command(self._input_generator.source_language, "generator")
                generation_command.extend([self._input_generation_parameters])
                job = JobModel(command=generation_command, stdout_filename="output.txt")
                job.add_file(file_model=self._input_generator.compiled_file(), filename="generator",
                             type=JobFile.EXECUTABLE)
                job_file = job.mark_file_for_extraction(filename="output.txt")
                job.run()
                self._input_file = job_file.file_model
                self.save()
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

        if self._output_static is False:
            if self._solution is None:
                raise AssertionError("test case does not have solution")
            else:
                self._output_file = run_with_input(
                    self._solution,
                    self.input_file,
                    self.problem.problem_data.time_limit,
                    self.problem.problem_data.memory_limit
                )[0]
                self.save()
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
                return self._output_file
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
            return self._input_file is not None


class Subtask(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"), related_name="subtasks")
    name = models.CharField(max_length=100, verbose_name=_("name"))
    score = models.IntegerField(verbose_name=_("score"))

    testcases = models.ManyToManyField(TestCase, related_name="subtasks")
