# Amir Keivan Mohtashami

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
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
from tasks.models import Task
import shlex

logger = logging.getLogger(__name__)


__all__ = ["TestCase", "Subtask", "Script", "InputGenerator"]


class InputGenerator(SourceFile):
    pass


class TestCaseGeneration(Task):
    testcase = models.ForeignKey("TestCase")

    def run(self):
        self.testcase.generate()


class Subtask(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"), related_name="subtasks")
    name = models.CharField(max_length=100, verbose_name=_("name"))
    score = models.IntegerField(verbose_name=_("score"))


class Script(RevisionObject):

    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    title = models.CharField(verbose_name=_("title"), max_length=256)
    script = models.TextField(verbose_name=_("script"))  # TODO: Validate the script using validators
    disabled = models.BooleanField(verbose_name=_("disabled"), default=False)

    def create_tests(self):
        # TODO: Handle subtasks
        self.testcase_set.all().delete()
        lines = self.script.split("\n")
        testcases = []
        for line in lines:
            line = line.strip()
            if not line or len(line) == 0:
                continue
            data = self.create_from_script_line(line)
            testcases.append(
                TestCase(
                    problem=self.problem,
                    _input_static=False,
                    _output_static=False,
                    **data
                )
            )
        TestCase.objects.bulk_create(testcases)

    @classmethod
    def get_generation_parameters_from_script_line(cls, line):
        line_split = shlex.split(line)
        data = dict()
        data["_input_generator_name"] = line_split[0]

        if len(line_split) >= 3 and line_split[-2] == ">":
            data["name"] = line_split[-1]
            line_split = line_split[:-1]

        data["_input_generation_parameters"] = shlex.quote(line_split[1:])

        return data

    def save(self, *args, **kwargs):
        super(Script, self).save(*args, **kwargs)
        if self.disabled:
            self.testcase_set.all().delete()
        else:
            self.create_tests()


class TestCase(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=20, verbose_name=_("name"), blank=True, editable=False)
    testcase_number = models.IntegerField(verbose_name=_("testcase_number"))

    _input_static = models.BooleanField(
        editable=False,
    )
    _output_static = models.BooleanField(
        editable=False,
    )

    # Input-related fields
    _input_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("input uploaded file"), null=True,
                                             related_name='+', blank=True)

    _input_generation_parameters = models.TextField(
        verbose_name=_("input generation command"),
        max_length=100,
        blank=True
    )
    _input_generator_name = models.CharField(verbose_name=_("generator"), null=True, blank=True, max_length=256)
    _input_generated_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+', blank=True)
    _input_generation_log = models.TextField(verbose_name=_("input generation log"))
    _input_generation_successful = models.NullBooleanField(verbose_name=_("successful input generation"))

    # Output-related fields
    _output_uploaded_file = models.ForeignKey(FileModel, verbose_name=_("output uploaded file"), null=True, related_name='+', blank=True)

    _output_generated_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+', blank=True)
    _output_generation_log = models.TextField(verbose_name=_("output generation log"))
    _output_generation_successful = models.NullBooleanField(verbose_name=_("successful output generation"))

    # TODO: Add output_verified: each output must be verified either automatically
    # (e.g. by running checker on the test) or manually.

    # TODO: Add generator_hint, output_mixer: Each generator will accept a file-name as argument. It may write
    # some hints in the file. Output-mixer, using the generator's hint and solution's output
    # (if provided with a solution), will generate the final output.

    # TODO: Add ability to automatically put the test in all subtasks
    # which their validators accept it

    script = models.ForeignKey(Script, null=True)

    subtasks = models.ManyToManyField(Subtask, related_name="testcases")

    judge_code = models.CharField(verbose_name=_("judge code"), editable=False, max_length=128, null=True)

    def get_judge_code(self, judge=None):
        if judge is None:
            judge = Judge.get_judge()
        self.judge_code = judge.add_testcase(
            problem_code=self.problem.get_judge_code(),
            testcase_id=self.pk,
            input_file=self.input_file,
            time_limit=self.problem.problem_data.time_limit,
            memory_limit=self.problem.problem_data.memory_limit,
        )
        self.save()
        return self.judge_code

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
            self._input_static = True
        elif self._input_generator_name is not None:
            self._input_static = False
        else:
            # Since a model must be cleaned before saving and this is checked in the validation method,
            # we simply ignore it here in order to avoid problems with django-clone
            pass

        if self._output_uploaded_file is not None:
            self._output_static = True
        else:
            self._output_static = False

        if getattr(self, "testcase_number", None) is None:
            current_number = self.problem.testcase_set.all().aggregate(Max('testcase_number'))["testcase_number__max"]
            if current_number is None:
                current_number = 0
            self.testcase_number = current_number + 1

        if not self.name or len(self.name) == 0:
            self.name = "auto_{}".format(str(self.testcase_number))

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
        if self._input_static or self.input_file_generated():
            return

        if self._input_generator_name is None:
            logger.error("A testcase has neither a generator nor a static input")
            self._input_generation_log = "Generation failed. No generator specified."
            self._input_generation_successful = False
        elif self._input_generator is None:
            self._input_generation_log = "Generation failed. Generator {} not found".format(
                self._input_generator_name,
            )
            self._input_generation_successful = False
        else:
            generation_command = get_execution_command(self._input_generator.source_language, "generator")
            generation_command.extend(shlex.split(self._input_generation_parameters))
            stdout_redirect = "output.txt"

            try:
                generator_compiled = self._input_generator.compiled_file()
            except:
                self._input_generation_log = "Generation failed. Generator didn't compile"
                self.save()
                return

            action = ActionDescription(
                commands=[generation_command],
                executables=[("generator", generator_compiled)],
                stdout_redirect=stdout_redirect,
                output_files=[stdout_redirect],
                time_limit=settings.DEFAULT_GENERATOR_TIME_LIMIT,
                memory_limit=settings.DEFAULT_GENERATOR_MEMORY_LIMIT
            )
            success, execution_success, outputs, sandbox_datas = execute_with_input(action)
            if not success:
                logger.error("Generating input for testcase {} failed.\n Sandbox data:\n{}".format(
                    str(self),
                    str(sandbox_datas[0]))
                )
                self._input_generation_log = "System failed to generate the input. Check the logs for more details. " \
                                       "This issue must be resolved by a system administrator"
                self._input_generation_successful = False
            elif not execution_success:
                self._input_generation_log = "Generation failed. Generator exited with exit code {}.".format(
                    sandbox_datas["exit_code"]
                )
                self._input_generation_successful = False
            else:
                self._input_generated_file = outputs[stdout_redirect]
                self._input_generation_log = "Generation successful."
                self._input_generation_successful = True
        self.save()


    @property
    def input_file(self):
        """
        returns a File instance of the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """

        if self._input_static is False:
            if not self._input_generation_successful:
                self.generate()
            return self._input_generated_file
        else:
            return self._input_uploaded_file

    def _generate_output_file(self):
        """
        In case the output is not static, generates the output using the generation command
        """

        if self._output_static or self.output_file_generated():
            return

        if not self.input_file_generated():
            logger.warning("Tried generating output before a successful generation of input")
            self._output_generation_log = "Generation failed. Input hasn't been generated yet"
            self._output_generation_successful = False
        else:
            solution = self.problem.problem_data.model_solution
            if solution is None:
                self._output_generation_log = "Generation failed. No model solution specified."
                self._output_generation_successful = False
            else:
                problem_code = self.problem.get_judge_code()
                testcase_code = self.get_judge_code()
                judge = Judge.get_judge()
                if solution.language not in judge.get_supported_languages():
                    self._output_generation_log = \
                        "Generation failed. Solution language is not supported by the judge"
                    self._output_generation_successful = False
                else:
                    evaluation_result = judge.generate_output(
                        problem_code,
                        solution.language,
                        [(solution.name, solution.code)],
                        testcase_code
                    )
                    if not evaluation_result.success:
                        self._output_generation_log = \
                            "Generation failed. Judge couldn't execute the solution."
                        self._output_generation_successful = False
                    elif evaluation_result.verdict != JudgeVerdict.ok:
                        self._output_generation_log = \
                            "Generation failed. Solution exited with verdict {} on the judge".format(
                                str(evaluation_result.verdict.name)
                            )
                        self._output_generation_successful = False
                    else:
                        self._output_generation_log = "Generation successful"
                        self._output_generation_successful = True
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
        if self._output_static is False:
            if not self._output_generation_successful:
                self.generate()
            return self._output_generated_file
        else:
            return self._output_uploaded_file

    def output_file_generated(self):
        if self._output_static is True:
            return True
        else:
            return self._output_generation_successful

    def input_file_generated(self):
        if self._input_static is True:
            return True
        else:
            return self._input_generation_successful

    def __str__(self):
        return self.name
