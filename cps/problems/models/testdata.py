# Amir Keivan Mohtashami

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Q
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from judge import Judge
from judge.results import JudgeVerdict
from problems.models import RevisionObject, SourceFile
from problems.models.problem import ProblemRevision
from runner import get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.execute_with_input import execute_with_input
from tasks.decorators import allow_async_method
from tasks.models import Task, State
import shlex

logger = logging.getLogger(__name__)


__all__ = ["TestCase", "Subtask", "InputGenerator"]


class InputGenerator(SourceFile):
    text_data = models.TextField(blank=True, null=False)
    is_enabled = models.BooleanField(default=False)

    @classmethod
    def get_generation_parameters_from_script_line(cls, problem, input_line):
        line_split = shlex.split(input_line)
        data = dict()

        test_name_separator_index = line_split.index(">")

        data["name"] = line_split[test_name_separator_index + 1]

        subtask_names = [
            line_split[subtask_index] for subtask_index in
            range(test_name_separator_index + 3, len(line_split), 2)
        ]
        data["subtasks"] = [
            problem.subtasks.get(name=name)
            for name in subtask_names
        ]

        data["_input_generation_parameters"] = " ".join(
            shlex.quote(line) for line in line_split[0:test_name_separator_index]
        )

        return data

    def _create_test(self, command):
        data = self.get_generation_parameters_from_script_line(self.problem, command)
        subtasks = data.pop("subtasks")

        test_case = TestCase(
                    problem=self.problem,
                    generator=self,
                    _input_generator_name=self.name,
                    input_static=False,
                    output_static=False,
                    **data)

        test_case.save()
        test_case.subtasks.add(*subtasks)

    def delete_testcases(self):
        TestCase.objects.filter(generator=self).delete()

    def generate_testcases(self):
        self.delete_testcases()
        for command in self.text_data.split("\n"):
            command = command.strip()
            if command:
                self._create_test(command)

    def enable(self):
        self.generate_testcases()
        self.is_enabled = True
        self.save()

    def disable(self):
        self.delete_testcases()
        self.is_enabled = False
        self.save()

class TestCaseValidation(Task):
    testcase = models.ForeignKey("TestCase")
    validator = models.ForeignKey("Validator")

    def run(self):
        self.validator.validate_testcase(self.testcase)

    @classmethod
    def create_and_run_all_for_testcase(cls, testcase):
        for validator in testcase.validators:
            cls.objects.create(
                    testcase=testcase,
                    validator=validator
            ).apply_async()

    @classmethod
    def create_and_run_all_for_validator(cls, validator):
        for testcase in validator.testcases:
            cls.objects.create(
                    testcase=testcase,
                    validator=validator
            ).apply_async()


class TestCaseGeneration(Task):
    testcase = models.ForeignKey("TestCase")

    def run(self):
        self.testcase.generate()
        TestCaseValidation.create_and_run_all_for_testcase(self.testcase)


class TestCase(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=20, verbose_name=_("name"), blank=True, editable=False, db_index=True)
    testcase_number = models.IntegerField(verbose_name=_("testcase_number"))
    # FIXME: Better naming for this
    generator = models.ForeignKey(InputGenerator, null=True, on_delete=models.CASCADE)

    input_static = models.BooleanField(
        editable=False,
    )
    output_static = models.BooleanField(
        editable=False,
    )

    # Input-related fields
    _input_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("input uploaded file"), null=True,
                                             related_name='+', blank=True)

    _input_generation_parameters = models.TextField(
        verbose_name=_("input generation command"),
        max_length=100,
        blank=True,
        null=True
    )
    _input_generator_name = models.CharField(verbose_name=_("generator"), null=True, blank=True, max_length=256)
    _input_generated_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+', blank=True)
    input_generation_log = models.TextField(verbose_name=_("input generation log"), null=True)
    input_generation_successful = models.NullBooleanField(verbose_name=_("successful input generation"))

    # Output-related fields
    _output_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("output uploaded file"), null=True, related_name='+', blank=True)

    _output_generated_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+', blank=True)
    output_generation_log = models.TextField(verbose_name=_("output generation log"), null=True)
    output_generation_successful = models.NullBooleanField(verbose_name=_("successful output generation"))

    # TODO: Add output_verified: each output must be verified either automatically
    # (e.g. by running checker on the test) or manually.

    # TODO: Add generator_hint, output_mixer: Each generator will accept a file-name as argument. It may write
    # some hints in the file. Output-mixer, using the generator's hint and solution's output
    # (if provided with a solution), will generate the final output.

    # TODO: Add ability to automatically put the test in all subtasks
    # which their validators accept it

    judge_code = models.CharField(verbose_name=_("judge code"), editable=False, max_length=128, null=True)

    def get_judge_code(self):
        if self.judge_code:
            return self.judge_code
        judge = Judge.get_judge()
        input_file = self.input_file
        if not input_file:
            return None
        self.judge_code = judge.add_testcase(
            problem_code=self.problem.get_judge_code(),
            testcase_id=self.pk,
            input_file=self.input_file,
            time_limit=self.problem.problem_data.time_limit,
            memory_limit=self.problem.problem_data.memory_limit,
        )
        self.save()
        return self.judge_code

    @property
    def input_generation_command(self):
        return "{} {}".format(self._input_generator_name, self._input_generation_parameters)

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def clean(self):
        if self._input_uploaded_file is None and self._input_generator_name is None:
            raise ValidationError("Either a static input or a generator must be set")
        if self._input_uploaded_file is not None and self._input_generator_name is not None:
            raise ValidationError("Only one of generator and static input file must be present.")

    def save(self, *args, **kwargs):
        """
        We first determine whether input and output is a static file and then continue saving process normally.
        """

        if self._input_uploaded_file is not None:
            self.input_static = True
        elif self._input_generator_name is not None:
            self.input_static = False
        else:
            # Since a model must be cleaned before saving and this is checked in the validation method,
            # we simply ignore it here in order to avoid problems with django-clone
            pass

        if self._output_uploaded_file is not None:
            self.output_static = True
        else:
            self.output_static = False

        if getattr(self, "testcase_number", None) is None:
            current_number = self.problem.testcase_set.all().aggregate(Max('testcase_number'))["testcase_number__max"]
            if current_number is None:
                current_number = 0
            self.testcase_number = current_number + 1

        if not self.name or len(self.name) == 0:
            self.name = "test_{0:3d}".format(self.testcase_number)

        super(TestCase, self).save(*args, **kwargs)

    @property
    def _input_generator(self):
        try:
            return self.problem.inputgenerator_set.get(name=self._input_generator_name)
        except InputGenerator.DoesNotExist:
            return None

    def _generate_input_file(self):
        """
        In case the input is not static, generates the input using the generation command
        """
        if self.input_static:
            return

        if self._input_generator_name is None:
            logger.error("A testcase has neither a generator nor a static input")
            self.input_generation_log = "Generation failed. No generator specified."
            self.input_generation_successful = False
        elif self._input_generator is None:
            self.input_generation_log = "Generation failed. Generator {} not found".format(
                self._input_generator_name,
            )
            self.input_generation_successful = False
        else:
            generation_command = get_execution_command(self._input_generator.source_language, "generator")
            generation_command.extend(shlex.split(self._input_generation_parameters))
            stdout_redirect = "output.txt"

            try:
                generator_compiled = self._input_generator.compiled_file()
            except:
                self.input_generation_log = "Generation failed. Generator didn't compile"
                self.save()
                return

            action = ActionDescription(
                commands=[generation_command],
                executables=[("generator", generator_compiled)],
                stdout_redirect=stdout_redirect,
                output_files=[stdout_redirect],
                time_limit=settings.FAILSAFE_TIME_LIMIT,
                memory_limit=settings.FAILSAFE_MEMORY_LIMIT
            )
            success, execution_success, outputs, sandbox_datas = execute_with_input(action)
            if not success:
                logger.error("Generating input for testcase {} failed.\n Sandbox data:\n{}".format(
                    str(self),
                    str(sandbox_datas[0]))
                )
                self.input_generation_log = \
                    "System failed to generate the input. " \
                    "Check the logs for more details. " \
                    "This issue must be resolved by a system administrator"
                self.input_generation_successful = False
            elif not execution_success:
                self.input_generation_log = "Generation failed. Generator exited with exit code {}.".format(
                    sandbox_datas["exit_code"]
                )
                self.input_generation_successful = False
            else:
                self._input_generated_file = outputs[stdout_redirect]
                self.input_generation_log = "Generation successful."
                self.input_generation_successful = True
        self.save()

    @property
    def input_file(self):
        """
        returns a File instance of the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """

        if self.input_static is False:
            if not self.input_file_generated():
                self._generate_input_file()
            return self._input_generated_file
        else:
            return self._input_uploaded_file

    @property
    def validators(self):
        global_validators = Q(global_validator=True)
        validators_for_subtasks = Q(_subtasks__in=self.subtasks.all())
        return self.problem.validator_set.filter(
                global_validators | validators_for_subtasks
        ).all()

    def validate_input_file(self):
        for validator in self.validators:
            validator.validate_testcase(self)

    def input_file_validated(self):
        for validator in self.validators:
            if not validator.get_or_create_testcase_result(self).valid:
                return False

        return True

    @property
    def solution(self):
        return self.problem.problem_data.model_solution

    def _generate_output_file(self):
        """
        In case the output is not static, generates the output using the generation command
        """

        if self.output_static:
            return

        if not self.input_file_generated():
            self._generate_input_file()
        if not self.input_file_generated():
            self.output_generation_log = "Generation failed. Input couldn't be generated"
            self.output_generation_successful = False
        else:
            solution = self.solution
            if solution is None:
                self.output_generation_log = "Generation failed. No model solution specified."
                self.output_generation_successful = False
            else:
                problem_code = self.problem.get_judge_code()
                testcase_code = self.get_judge_code()
                judge = Judge.get_judge()
                if solution.language not in judge.get_supported_languages():
                    self.output_generation_log = \
                        "Generation failed. Solution language is not supported by the judge"
                    self.output_generation_successful = False
                else:
                    evaluation_result = judge.generate_output(
                        problem_code,
                        solution.language,
                        [(solution.name, solution.code)],
                        testcase_code
                    )
                    if not evaluation_result.success:
                        self.output_generation_log = \
                            "Generation failed. Judge couldn't execute the solution."
                        self.output_generation_successful = False
                    elif evaluation_result.verdict != JudgeVerdict.ok:
                        self.output_generation_log = \
                            "Generation failed. Solution exited with verdict {} on the judge".format(
                                str(evaluation_result.verdict.name)
                            )
                        self.output_generation_successful = False
                    else:
                        self.output_generation_log = "Generation successful"
                        self.output_generation_successful = True
                        self._output_generated_file = evaluation_result.output_file
        self.save()

    def generate(self):
        # TODO: Only generate if a generation process hasn't started yet
        self._generate_input_file()
        if self.input_file_generated():
            self._generate_output_file()

    @property
    def output_file(self):
        """
        returns a File instance for the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """
        if self.output_static is False:
            if not self.output_generation_successful:
                self.generate()
            return self._output_generated_file
        else:
            return self._output_uploaded_file

    def output_file_generated(self):
        if self.output_static is True:
            return True
        else:
            return self.output_generation_successful

    def input_file_generated(self):
        if self.input_static is True:
            return True
        else:
            return self.input_generation_successful

    def _invalidate_output(self, commit=True):
        self.output_generation_log = None
        self._output_generated_file = None
        self.output_generation_successful = None
        if commit:
            self.save()

    def _invalidate_input(self, commit=True):
        self.input_generation_log = None
        self._input_generated_file = None
        self.input_generation_successful = None
        if commit:
            self.save()

    def _invalidate_validation(self):
        self.validation_results.all().delete()

    def invalidate(self):
        self._invalidate_output(commit=False)
        self._invalidate_validation()
        self._invalidate_input(commit=False)
        self.judge_code = None
        self.save()

    def has_errors(self):
        input_generation_failed = not self.input_file_generated()
        output_generation_failed = not self.output_file_generated()
        input_validation_failed = not self.input_file_validated()

        failed = \
            input_generation_failed or \
            output_generation_failed or \
            input_validation_failed

        return failed

    def input_generation_completed(self):
        return self.input_generation_successful is not None or self.input_static

    def output_generation_completed(self):
        return self.output_generation_successful is not None or self.output_static

    def testcase_generation_completed(self):
        input_validation_tried =  \
            self.validation_results.filter(valid__isnull=False).count() == len(self.validators)

        return self.input_generation_completed() and \
            self.output_generation_completed() and \
            input_validation_tried

    def being_generated(self):
        return self.testcasegeneration_set.exclude(
            state=State.finished.name
        ).exclude(state__isnull=True).exists() or self.testcasevalidation_set.exclude(
            state=State.finished.name
        ).exclude(state__isnull=True).exists()

    def __str__(self):
        return self.name


class Subtask(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"), related_name="subtasks")
    name = models.CharField(max_length=100, verbose_name=_("name"), db_index=True)
    score = models.IntegerField(verbose_name=_("score"))
    testcases = models.ManyToManyField(TestCase, verbose_name=_("testcases"), related_name="subtasks")


    @staticmethod
    def get_matching_fields():
        return ["name"]

    def __str__(self):
        return self.name

    @property
    def validators(self):
        return self.problem.validator_set.filter(Q(global_validator=True) | Q(_subtasks=self))
