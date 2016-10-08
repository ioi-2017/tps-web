# Amir Keivan Mohtashami

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models import SourceFile, RevisionObject
from problems.models.problem import ProblemRevision
from problems.utils import run_with_input
from runner import get_execution_command
from runner.decorators import allow_async_method
from runner.models import JobModel, JobFile


__all__ = ["TestCase", "Subtask"]


class TestCase(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=20, verbose_name=_("name"), blank=True)
    testcase_number = models.IntegerField(verbose_name=_("testcase_number"))

    _input_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("input uploaded file"), null=True,
                                             related_name='+', blank=True)
    _input_generation_parameters = models.TextField(
        verbose_name=_("input generation command"),
        max_length=100,
        blank=True
    )
    _input_generator = models.ForeignKey(SourceFile, verbose_name=_("generator"), null=True, related_name='+', blank=True)
    _input_static = models.BooleanField(
        editable=False,
    )
    _input_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+')

    _output_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("output uploaded file"), null=True, related_name='+', blank=True)
    _output_static = models.BooleanField(
        editable=False,
    )
    _output_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+')
    _solution = models.ForeignKey(SourceFile, verbose_name=_("solution"), null=True, related_name='+', blank=True)

    def clean(self):
        if self._input_uploaded_file is None and self._input_generator is None:
            raise ValidationError("Either a static input or a generator must be set")
        if self._input_uploaded_file is not None and self._input_generator is not None:
            raise ValidationError("Only one of generator and static input file must be present.")

        if self._output_uploaded_file is None and self._solution is None:
            raise ValidationError("Either a static output or a solution must be set")
        if self._output_uploaded_file is not None and self._solution is not None:
            raise ValidationError("Only one of solution and static output file must be present.")

    def save(self, *args, **kwargs):
        """
        We first determine whether input and output is a static file and then continue saving process normally.
        """
        if self._input_uploaded_file is not None:
            if self._input_generator is not None:
                raise ValidationError("Validate the model before saving it")
            self._input_static = True
        elif self._input_generator is not None:
            self._input_static = False
        else:
            # Since a model must be cleaned before saving and this is checked in the validation method,
            # we can either do nothing here or raise an error as a fail-safe.
            raise ValidationError("Validate the model before saving it")

        if self._output_uploaded_file is not None:
            if self._solution is not None:
                raise ValidationError("Validate the model before saving it")
            self._output_static = True
        elif self._solution is not None:
            self._output_static = False
        else:
            raise ValidationError("Validate the model before saving it")

        current_number = TestCase.objects.all().aggregate(Max('testcase_number'))["testcase_number__max"]
        if current_number is None:
            current_number = 0
        self.testcase_number =  current_number + 1

        if self.name == "":
            self.name = "test" + str(self.testcase_number)

        super(TestCase, self).save(*args, **kwargs)

    @allow_async_method
    def generate_input_file(self):
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
                self.generate_input_file.async()
                return None
        else:
            return self._input_uploaded_file

    @allow_async_method
    def generate_output_file(self):
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
                self.generate_output_file.async(self)
                return None
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


class Subtask(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"), related_name="subtasks")
    name = models.CharField(max_length=100, verbose_name=_("name"))
    score = models.IntegerField(verbose_name=_("score"))

    testcases = models.ManyToManyField(TestCase, related_name="subtasks")
