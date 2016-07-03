# Amir Keivan Mohtashami
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from file_repository.models import File
from problems.models.problem import ProblemRevision
from version_control.models import VersionModel


class TestCase(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=20, verbose_name=_("name"))

    _input_uploaded_file = models.ForeignKey(File, verbose_name=_("input uploaded file"), null=True, related_name='+')
    # TODO: Add a validator for _input_generation_command to validate that command is in the right form
    _input_generation_command = models.TextField(
        verbose_name=_("input generation command"),
        max_length=1,
        null=True,
        blank=True
    )
    _input_static = models.BooleanField(
        editable=False,
    )
    _input_file = models.ForeignKey(File, editable=False, related_name='+')

    _output_uploaded_file = models.ForeignKey(File, verbose_name=_("input file"), null=True, related_name='+')
    _output_static = models.BooleanField(
        editable=False,
    )
    _output_file = models.ForeignKey(File, editable=False, related_name='+')

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
        raise NotImplementedError("This must be implemented")

    def generate_input_file(self):
        """
        This method is used to request generation of input file.
        As the generation process is done asynchronously it is only responsible to add the generation task
         (self._generate_input_file) to workers queue
        """
        raise NotImplementedError("This must be implemented")

    @property
    def input_file(self):
        """
        returns a File instance of the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """
        raise NotImplementedError("This must be implemented")

    def _generate_output_file(self):
        """
        In case the output is not static, generates the output using the generation command
        """
        raise NotImplementedError("This must be implemented")

    def generate_output_file(self):
        """
        This method is used to request generation of output file.
        As the generation process is done asynchronously it is only responsible to add the generation task
         (self._generate_output_file) to workers queue
        """
        raise NotImplementedError("This must be implemented")

    @property
    def output_file(self):
        """
        returns a File instance for the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """
        raise NotImplementedError("This must be implemented")


class Subtask(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"), related_name="subtasks")
    name = models.CharField(max_length=100, verbose_name=_("name"))
    score = models.IntegerField(verbose_name=_("score"))

    testcases = models.ManyToManyField(TestCase, related_name="subtasks")



