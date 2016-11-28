# Amir Keivan Mohtashami

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models import RevisionObject
from problems.models.file import SourceFile
from problems.models.problem import ProblemRevision
from problems.models.testdata import Subtask, TestCase
from runner import get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.execute_with_input import execute_with_input
from runner.sandbox.utils import get_exit_status_human_translation
from tasks.decorators import allow_async_method
from tasks.models import Task

__all__ = ["Validator", "ValidatorResult"]

class Validator(SourceFile):

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

    def validate(self):
        """
        This method is used to validate the testcases in the given subtasks.
        If subtasks is None, it is replaced by self.subtasks
        """
        if self.global_validator:
            testcases = self.problem.testcase_set.all()
        else:
            testcases = self.problem.testcase_set.filter(subtasks__in=self._subtasks.all()).all()

        for testcase in testcases:
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
        validator_result.apply_async()


class ValidatorResult(Task):
    exit_status = models.CharField(max_length=200, verbose_name=_("exit status"), null=True)
    valid = models.NullBooleanField(verbose_name=_("valid"))
    executed = models.BooleanField(verbose_name=_("executed"), default=False)
    validation_message = models.TextField(verbose_name=_("validation message"))

    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    validator = models.ForeignKey(Validator, verbose_name=_("validator"))

    class Meta:
        unique_together = ("testcase", "validator")

    def run(self):
        validation_command = get_execution_command(self.validator.source_language, "validator")
        validation_command.append("input.txt")
        validator_compiled_file = self.validator.compiled_file()

        if validator_compiled_file is None:
            self.validation_message = "Validation failed. Validator didn't compile"
            self.valid = False
            self.executed = True
            self.exit_status = "Compilation Error"
            self.save()
            return
        action = ActionDescription(
            commands=[validation_command],
            files=[("input.txt", self.testcase.input_file)],
            executables=[("validator", self.validator.compiled_file())],
            time_limit=settings.DEFAULT_GENERATOR_TIME_LIMIT,
            memory_limit=settings.DEFAULT_GENERATOR_MEMORY_LIMIT,
            stderr_redirect="stderr.txt",
            output_files=["stderr.txt"]
        )

        success, execution_success, outputs, data = execute_with_input(action)

        if success:
            self.exit_status = get_exit_status_human_translation(data[0]["exit_status"])
            self.valid = execution_success
            # FIXME: This probably should be done more properly
            stderr_file = outputs["stderr.txt"]
            self.validation_message = stderr_file.file.readline()
            stderr_file.delete()
        else:
            self.valid = False
            self.validation_message = "Validation failed due to system error. " \
                                      "Please inform the system administrator"
            self.exit_status = "System Error"
        self.executed = True
        self.save()