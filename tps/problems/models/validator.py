# Amir Keivan Mohtashami
import logging
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models.file import SourceFile
from runner import get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.execute_with_input import execute_with_input
from runner.sandbox.utils import get_exit_status_human_translation
from tasks.tasks import CeleryTask

__all__ = ["Validator", "ValidatorResult"]

logger = logging.getLogger(__name__)

class ValidatorResultComputationTask(CeleryTask):

    def validate_dependencies(self, validator_result):
        verdict = True
        if validator_result.validator.compilation_finished:
            if not validator_result.validator.compilation_successful():
                validator_result.valid = False
                validator_result.executed = True
                validator_result.validation_message = "Validator didn't compile. Log: {}".format(
                    validator_result.validator.last_compile_log
                )
                validator_result.save()
                return False
        else:
            logger.info("Waiting until validator {} is compiled".format(str(validator_result.validator)))
            validator_result.validator.compile()
            verdict = None

        if validator_result.testcase.input_generation_completed():
            if not validator_result.testcase.input_file_generated():
                validator_result.valid = False
                validator_result.executed = True
                validator_result.validation_message = "Input couldn't be generated"
                validator_result.save()
                return False
        else:
            logger.info("Waiting until testcase {} is generated".format(str(validator_result.testcase)))
            validator_result.testcase.generate()
            verdict = None

        return verdict

    def execute(self, validator_result):
        validator_result._run()


class ValidatorResult(models.Model):
    exit_status = models.CharField(max_length=200, verbose_name=_("exit status"), null=True)
    valid = models.NullBooleanField(verbose_name=_("valid"), default=None)
    executed = models.BooleanField(verbose_name=_("executed"), default=False)
    validation_message = models.TextField(verbose_name=_("validation message"))

    task_id = models.CharField(verbose_name=_("task id"), max_length=128, null=True)

    testcase = models.ForeignKey("self", verbose_name=_("testcase"), related_name="validation_results")
    validator = models.ForeignKey("self", verbose_name=_("validator"), related_name="results")

    class Meta:
        unique_together = ("testcase", "validator")

    def run(self):
        if self.task_id is None:
            self.task_id = ValidatorResultComputationTask().delay(self).id
            self.save()

    def _run(self):
        # TODO: Make sure testcase has already been generated
        validation_command = get_execution_command(self.validator.source_language, "validator")
        validation_command.append("input.txt")
        validator_compiled_file = self.validator.compiled_file

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
            executables=[("validator", self.validator.compiled_file)],
            time_limit=settings.FAILSAFE_TIME_LIMIT,
            memory_limit=settings.FAILSAFE_MEMORY_LIMIT,
            stdin_redirect="input.txt",
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

    #_subtasks = models.ManyToManyField("Subtask", verbose_name=_("subtasks"), blank=True)
    #global_validator = models.BooleanField(
    #    verbose_name=_("all subtasks"),
    #    help_text=_("if marked, it validates all subtasks")
    #)
    global_validator = False

    class Meta:
        storage_name = "validator"

    def get_value_as_dict(self):
        d = super(Validator, self).get_value_as_dict()
        d["subtasks"] = ','.join(sorted([str(s) for s in self.subtasks]))
        return d

    @property
    def testcases(self):
        testcases = []
        if self.global_validator:
            testcases = self.problem.testcase_set.all()
        else:
            mark = set([])
            for subtask in self.subtasks.all():
                for testcase in subtask.testcases.all():
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
        validator_result, _ = ValidatorResult.objects.get_or_create(
                testcase=testcase,
                validator=self
        )
        return validator_result

    def invalidate(self):
        self.results.all().delete()

    def clone_relations(self, cloned_instances, ignored_instances):
        if self in ignored_instances:
            return
        subtasks = []
        for subtask in self._subtasks.all():
            subtasks.append(cloned_instances[subtask])
        cloned_instances[self]._subtasks.clear()
        if len(subtasks) > 0:
            cloned_instances[self]._subtasks.add(*subtasks)
