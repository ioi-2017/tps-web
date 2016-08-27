# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models.file import SourceFile
from problems.models.problem import ProblemRevision
from problems.models.testdata import Subtask, TestCase
from runner import get_execution_command
from runner.decorators import run_on_worker
from runner.models import JobModel, JobFile
from version_control.models import VersionModel


class Validator(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    code = models.OneToOneField(SourceFile, verbose_name=_("source code"))
    _subtasks = models.ManyToManyField(Subtask, verbose_name=_("subtasks"))
    _validate_all_subtasks = models.BooleanField(
        verbose_name=_("all subtasks"),
        help_text=_("if marked, it validates all subtasks")
    )

    @property
    def subtasks(self):
        if self._validate_all_subtasks:
            return self.problem.subtasks.all()
        else:
            return self._subtasks

    def validate_subtasks(self, subtasks=None):
        """
        This method is used to validate the testcases in the given subtasks.
        If subtasks is None, it is replaced by self.subtasks
        """
        if subtasks is None:
            subtasks = self.subtasks
        for subtask in subtasks.all():
            for testcase in subtask.testcases.all():
                self.validate_testcase(testcase)

    def validate_testcase(self, testcase):
        """
        This method is used to validate one testcase.
        """
        try:
            old_validator_result = ValidatorResult.objects.get(testcase=testcase, validator=self)
            old_validator_result.delete()
        except:
            pass
        validator_result = ValidatorResult(testcase=testcase, validator=self)
        validator_result.save()
        validator_result.run()

class ValidatorResult(VersionModel):
    exit_code = models.CharField(max_length=200, verbose_name=_("exit code"))
    exit_status = models.CharField(max_length=200, verbose_name=_("exit status"))
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    validator = models.ForeignKey(Validator, verbose_name=_("validator"))

    @run_on_worker
    def run(self):
        validation_command = get_execution_command(self.validator.code.source_language, "validator")

        job = JobModel(command=validation_command)
        job.add_file(file_model=self.testcase.input_file, filename="input.txt", type=JobFile.READONLY)
        job.add_file(file_model=self.validator.code.compiled_file(), filename="validator", type=JobFile.EXECUTABLE)
        job.run()
        self.exit_code = job.exit_code
        self.exit_status = job.exit_status
        self.save()