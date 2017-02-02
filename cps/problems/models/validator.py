# Amir Keivan Mohtashami

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models.file import SourceFile
from runner import get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.execute_with_input import execute_with_input
from runner.sandbox.utils import get_exit_status_human_translation


__all__ = ["Validator", "ValidatorResult"]


class ValidatorResult(models.Model):
    exit_status = models.CharField(max_length=200, verbose_name=_("exit status"), null=True)
    valid = models.NullBooleanField(verbose_name=_("valid"), default=None)
    executed = models.BooleanField(verbose_name=_("executed"), default=False)
    validation_message = models.TextField(verbose_name=_("validation message"))

    testcase = models.ForeignKey("TestCase", verbose_name=_("testcase"), related_name="validation_results")
    validator = models.ForeignKey("Validator", verbose_name=_("validator"), related_name="results")

    class Meta:
        unique_together = ("testcase", "validator")

    @classmethod
    def get_or_create(cls, validator, testcase):
        try:
            return cls.objects.get(validator=validator, testcase=testcase)
        except cls.DoesNotExist:
            return cls.objects.create(validator=validator, testcase=testcase)

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
            time_limit=settings.FAILSAFE_TIME_LIMIT,
            memory_limit=settings.FAILSAFE_MEMORY_LIMIT,
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


class Validator(SourceFile):

    _subtasks = models.ManyToManyField("Subtask", verbose_name=_("subtasks"), blank=True)
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

    @property
    def testcases(self):
        testcases = []
        if self.global_validator:
            testcases = self.problem.testcase_set.all()
        else:
            mark = set([])
            for subtask in self._subtasks.all():
                for testcase in subtask.testcases:
                    if not testcase.pk in mark:
                        testcases.append(testcase)
                        mark.update([testcase.pk])
        return testcases

    def validate(self):
        """
        This method is used to validate the testcases in the given subtasks.
        If subtasks is None, it is replaced by self.subtasks
        """
        for testcase in self.testcases:
            self.validate_testcase(testcase)

    def validate_testcase(self, testcase, force_recreate=False):
        """
        This method is used to validate one testcase.
        """
        if force_recreate:
            try:
                self.results.get(testcase=testcase).delete()
            except ValidatorResult.DoesNotExist:
                pass
        validator_result = self.get_or_create_testcase_result(testcase)
        validator_result.run()

    def get_or_create_testcase_result(self, testcase):
        return ValidatorResult.get_or_create(
                testcase=testcase,
                validator=self
        )

    def invalidate(self):
        self.results.all().delete()
