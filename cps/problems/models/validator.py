# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models import RevisionObject
from problems.models.file import SourceFile
from problems.models.problem import ProblemRevision
from problems.models.testdata import Subtask, TestCase
from runner import get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.execute_with_input import execute_with_input
from runner.decorators import allow_async_method

from django.conf import settings

__all__ = ["Validator", "ValidatorResult"]

class Validator(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    code = models.ForeignKey(SourceFile, verbose_name=_("source code"))
    _subtasks = models.ManyToManyField(Subtask, verbose_name=_("subtasks"))
    global_validator = models.BooleanField(
        verbose_name=_("all subtasks"),
        help_text=_("if marked, it validates all subtasks")
    )

    @property
    def subtasks(self):
        if self.global_validator:
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

class ValidatorResult(RevisionObject):
    exit_code = models.CharField(max_length=200, verbose_name=_("exit code"), null=True)
    exit_status = models.CharField(max_length=200, verbose_name=_("exit status"), null=True)
    valid = models.NullBooleanField(verbose_name=_("valid"))
    executed = models.BooleanField(verbose_name=_("executed"), default=False)

    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    validator = models.ForeignKey(Validator, verbose_name=_("validator"))

    @allow_async_method
    def run(self):
        validation_command = get_execution_command(self.validator.code.source_language, "validator")

        action = ActionDescription(
            commands=[validation_command],
            files=[("input.txt", self.testcase.input_file)],
            executables=[("validator", self.validator.code.compiled_file())],
            time_limit=settings.DEFAULT_GENERATOR_TIME_LIMIT,
            memory_limit=settings.DEFAULT_GENERATOR_MEMORY_LIMIT,
        )

        success, execution_success, outputs, data = execute_with_input(action)
        if success:
            self.exit_code = data[0]["exit_code"]
            self.exit_status = data[0]["exit_status"]
            self.valid = execution_success
        self.executed = True
        self.save()
