# Amir Keivan Mohtashami
import json
import logging
import os
import shlex
import django

from celery.result import AsyncResult
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max, Q
from django.utils.functional import cached_property, lazy_property
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel, FileSystemModel
from git_orm.models.fields import GitToGitManyToManyField
from judge.results import JudgeVerdict
from problems.models import RevisionObject, SourceFile, ProblemCommit
from problems.models.validator import Validator
from problems.models.fields import ReadOnlyGitToGitForeignKey
from problems.models.generic import ManuallyPopulatedModel, FileSystemPopulatedModel, JSONModel
from runner import get_execution_command
from runner.actions.action import ActionDescription
from runner.actions.execute_with_input import execute_with_input
from tasks.tasks import CeleryTask

from git_orm import models as git_models, GitError

logger = logging.getLogger(__name__)


__all__ = ["TestCase", "Subtask", "InputGenerator"]


class InputGenerator(SourceFile):
    text_data = models.TextField(blank=True, null=False)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        storage_name = "gen"

    @staticmethod
    def text_data_validator(problem, text):
        names = set()

        def line_valid(line_id, line):
            line = line.strip()
            if len(line) == 0:
                return
            line_split = shlex.split(line)

            if '>' not in line_split:
                raise ValidationError({
                    'text_data': ValidationError(_("line #%(line)s doesn't contains '>'."), code='invalid',
                                                 params={'line': line_id})
                })

            test_name_separator_index = line_split.index(">")

            if line_split[test_name_separator_index+1] in names:
                raise ValidationError({
                    'text_data': ValidationError(_("line #%(line)s's name is duplicated!"), code='invalid',
                                                 params={'line': i})
                })
            names.add(line_split[test_name_separator_index+1])

            for seperator_index in range(test_name_separator_index + 2, len(line_split), 2):
                if line_split[seperator_index] != '|':
                    raise ValidationError({
                        'text_data': ValidationError(_("in line #%(line)s, subtasks are not separated by '|'"),
                                                     code='invalid',
                                                     params={'line': line_id})
                    })

            for subtask_index in range(test_name_separator_index + 3, len(line_split), 2):
                subtask_name = line_split[subtask_index]
                if not problem.subtasks.filter(name=subtask_name).exists():
                    raise ValidationError({
                        'text_data': ValidationError(_("in line #%(line)s, subtask %(subtask)s doesn't exist."),
                                                     code='invalid',
                                                     params={'line': line_id, 'subtask': subtask_name})
                    })

        for i, line in enumerate(text.split("\n"), start=1):
            line_valid(i, line)

    def clean(self):
        try:
            InputGenerator.text_data_validator(self.problem, self.text_data)
        except ValidationError as v:
            raise v
        except Exception as e:
            raise ValidationError({
                'text_data': ValidationError(_("data format is incorrect!\ncorrect format: [params] > name | subtask1 | subtask2 | ..."))
            })

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
                try:
                    self._create_test(command)
                except django.db.utils.IntegrityError as e:
                    data = self.get_generation_parameters_from_script_line(self.problem, command)
                    raise ValidationError({
                        'text_data': ValidationError(_("A testcase with name {} already exist!".format(data['name'])))
                    })

    def enable(self):
        try:
            self.clean()
            self.generate_testcases()
        except ValidationError as e:
            self.disable()
            raise e
        except Exception as e:
            self.disable()
            raise e

        self.is_enabled = True
        self.save()
        return False

    def disable(self):
        self.delete_testcases()
        self.is_enabled = False
        self.save()

    def get_value_as_dict(self):
        return {
            "code": self.file.get_value_as_string(),
            "data": self.text_data,
            "enabled": str(self.is_enabled),
        }

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        ls = super(InputGenerator, cls)._get_existing_primary_keys(transaction)
        return [pk for pk in ls if not (pk.endswith(".data") and pk[:-5] in ls)]

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = super(InputGenerator, cls)._get_instance(transaction, pk)
        try:
            data_path = list(obj.path)
            data_path[-1] += ".data"
            obj.text_data = transaction.get_blob(data_path).decode("utf-8")
        except GitError:
            pass
        return obj


class TestCaseInputGeneration(CeleryTask):
    def validate_dependencies(self, testcase):
        if not testcase.input_static:
            if testcase._input_generator.compilation_finished:
                if not testcase._input_generator.compilation_successful():
                    testcase.input_generation_successful = False
                    testcase.input_generation_log = "Generator didn't compile. Log:{}".format(
                        testcase._input_generator.last_compile_log
                    )
                    testcase.save()
                    return False
            else:
                logger.info("Waiting until input generator {} is compiled".format(str(testcase._input_generator)))
                testcase._input_generator.compile()
                return None
        return True

    def execute(self, testcase):
        testcase._generate_input_file()

    def execute_child_tasks(self, testcase):
        for validator in testcase.validators:
            validator.validate_testcase(testcase, force_recreate=True)
        testcase.output_generation_task_id = TestCaseOutputGeneration().delay(testcase)
        testcase.save()


class TestCaseOutputGeneration(CeleryTask):
    def validate_dependencies(self, testcase):
        if testcase.judge_initialization_completed():
            if not testcase.judge_initialization_successful:
                testcase.output_generation_log = "Judge couldn't be initialized. {}".format(
                    testcase.judge_initialization_message
                )
                testcase.output_generation_successful = False
                testcase.save()
                return False
        else:
            logger.info("Waiting until testcase {} is initialized in judge".format(str(testcase)))
            testcase.initialize_in_judge()
            return None

        return True

    def execute(self, testcase):
        testcase._generate_output_file()


class TestCaseJudgeInitialization(CeleryTask):
    def validate_dependencies(self, testcase):

        if not testcase.problem.judge_initialization_completed() or \
                not testcase.problem.judge_initialization_successful:
                    logger.info("Waiting until problem {} is initialized in judge".format(str(testcase.problem)))
                    testcase.problem.initialize_in_judge()
                    return None

        if testcase.input_generation_completed():
            if not testcase.input_file_generated():
                testcase.judge_initialization_message = "Input couldn't be generated."
                testcase.judge_initialization_successful = False
                testcase.save()
                return False
        else:
            testcase.generate()
            return None

        return True

    def execute(self, testcase):
        testcase._initialize_in_judge()


class TestCase(FileSystemPopulatedModel):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)
    name = models.CharField(max_length=20, verbose_name=_("name"),
                            blank=True, editable=False, db_index=True,
                            primary_key=True)
    testcase_number = models.IntegerField(verbose_name=_("testcase_number"))
    # FIXME: Better naming for this
    generator = ReadOnlyGitToGitForeignKey(InputGenerator, null=True, default=None)

    #input_static = models.BooleanField(editable=False,)
    input_static = True
    #output_static = models.BooleanField(editable=False,)
    output_static = True

    def get_storage_path(self):
        dir_path = os.path.join(self.problem.get_storage_path(), "tests")
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            # TODO: Consider auto-creation here when support for write is added
            raise self.InvalidObject("{} should be a directory".format(dir_path))
        return dir_path

    @property
    def get__input_uploaded_file_id(self):
        return os.path.join(self.get_storage_path(), self.pk + ".in")

    @property
    def get__output_uploaded_file_id(self):
        return os.path.join(self.get_storage_path(), self.pk + ".out")

    @property
    def path(self):
        return os.path.join(self.get_storage_path(), self.pk + ".desc")

    # Input-related fields
    _input_uploaded_file = ReadOnlyGitToGitForeignKey(FileSystemModel,
                                                      verbose_name=_("input uploaded file"), null=True,
                                                      related_name='+', blank=True)

    #_input_generation_parameters = models.TextField(
    #    verbose_name=_("input generation command"),
    #    max_length=100,
    #    blank=True,
    #    null=True
    #)
    #_input_generator_name = models.CharField(verbose_name=_("generator"), null=True, blank=True, max_length=256)
    #_input_generated_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+', blank=True)
    #_input_generated_file = None
    #input_generation_log = models.TextField(verbose_name=_("input generation log"), null=True)
    #input_generation_successful = models.NullBooleanField(verbose_name=_("successful input generation"))
    #input_generation_task_id = models.CharField(verbose_name=_("input generation task id"), max_length=128, null=True)

    # Output-related fields
    _output_uploaded_file = ReadOnlyGitToGitForeignKey(FileSystemModel,
                                                      verbose_name=_("output uploaded file"), null=True,
                                                      related_name='+', blank=True)

    #_output_generated_file = models.ForeignKey(FileModel, editable=False, null=True, related_name='+', blank=True)
    #_output_generated_file = None
    #output_generation_log = models.TextField(verbose_name=_("output generation log"), null=True)
    #output_generation_successful = models.NullBooleanField(verbose_name=_("successful output generation"))
    #output_generation_task_id = models.CharField(verbose_name=_("output generation task id"), max_length=128, null=True)

    # TODO: Add output_verified: each output must be verified either automatically
    # (e.g. by running checker on the test) or manually.

    # TODO: Add generator_hint, output_mixer: Each generator will accept a file-name as argument. It may write
    # some hints in the file. Output-mixer, using the generator's hint and solution's output
    # (if provided with a solution), will generate the final output.

    # TODO: Add ability to automatically put the test in all subtasks
    # which their validators accept it

    judge_initialization_task_id = models.CharField(verbose_name=_("initialization task id"), max_length=128, null=True)
    judge_initialization_successful = models.NullBooleanField(verbose_name=_("initialization finished"), default=None)
    judge_initialization_message = models.CharField(verbose_name=_("initialization message"), max_length=256)

    _subtasks = GitToGitManyToManyField("Subtask", verbose_name=_("subtasks"), related_name="+", blank=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("problem", "name",)
        index_together = ("problem", "name",)

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        problem = ProblemCommit.objects.with_transaction(transaction).get()
        dir_path = os.path.join(problem.get_storage_path(), "tests")
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            return []
        else:
            files = os.listdir(dir_path)
            inputs = []
            outputs = []
            for file in files:
                abs_path = os.path.join(dir_path, file)
                if os.path.isfile(abs_path):
                    if file.endswith(".in"):
                        inputs.append(file[:-3])
                    elif file.endswith(".out"):
                        outputs.append(file[:-4])
            return [key for key in inputs if key in outputs]

    @cached_property
    def subtasks(self):
        if self._subtasks.count() != 0:
            return self._subtasks
        mapping_file = os.path.join(self.get_storage_path(), "mapping")
        if os.path.exists(mapping_file):
            subtasks = []
            with open(mapping_file, "r") as file_:
                for line in file_.readlines():
                    try:
                        data = line.strip().split(' ')
                        subtask_name, testcase_name = data[0], data[1]
                        if testcase_name == self.name:
                            subtasks.append(subtask_name)
                    except Exception:
                        pass
            self._subtasks = subtasks
            self.save()
        return self._subtasks


    def _clean_for_clone(self, cloned_instances):
        super(TestCase, self)._clean_for_clone(cloned_instances)
        if self.generator:
            self.generator = cloned_instances[self.generator]

    def initialize_in_judge(self):
        if self.judge_initialization_task_id:
            if not self.judge_initialization_successful:
                result = AsyncResult(self.judge_initialization_task_id)
                if result.failed() or result.successful():
                    self.judge_initialization_task_id = None
                    self.save()
        if not self.judge_initialization_task_id:
            self.judge_initialization_task_id = TestCaseJudgeInitialization().delay(self).id
            self.save()

    def _initialize_in_judge(self):
        self.judge_initialization_successful, self.judge_initialization_message = \
            self.problem.get_task_type().add_testcase(
                problem_code=self.problem.get_judge_code(),
                testcase_code=self.name,
                input_file=self.input_file,
            )
        self.save()

    def judge_initialization_completed(self):
        return self.judge_initialization_successful is not None

    def get_judge_code(self):
        if not self.judge_initialization_successful:
            return None
        else:
            return str(self.name)

    @property
    def input_generation_command(self):
        return "{} {}".format(self._input_generator_name, self._input_generation_parameters)

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def get_value_as_dict(self):
        data = {}
        if self.input_static:
            data["input"] = self.input_file.get_value_as_string()
        else:
            data["input"] = self.input_generation_command

        if self.output_static:
            data["output"] = self.output_file.get_value_as_string()
        else:
            data["output"] = "Generated using {}".format(self.solution)
        if self.generator:
            data["generator"] = self.generator.name
        return data

    def clean(self):
        if self._input_uploaded_file is None and self._input_generator_name is None:
            raise ValidationError("Either a static input or a generator must be set")
        if self._input_uploaded_file is not None and self._input_generator_name is not None:
            raise ValidationError("Only one of generator and static input file must be present.")

    def deprecated_django_save(self, *args, **kwargs):
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
                generator_compiled = self._input_generator.compiled_file
            except:
                self.input_generation_log = "Generation failed. Generator didn't compile. Log: {}".format(
                    self._input_generator.last_compile_log
                )
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
                self.input_generation_log = "Generation failed. {}.".format(
                    str(sandbox_datas[0])
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
        if not self.input_file_generated():
            return None
        if self.input_static is False:
            return self._input_generated_file
        else:
            return self._input_uploaded_file

    @property
    def validators(self):
        ### FIXME: Return real list of validators
        return []
        global_validators = Q(global_validator=True)
        validators_for_subtasks = Q(_subtasks__in=self.subtasks.all())
        return self.problem.validator_set.filter(
            global_validators | validators_for_subtasks
        ).distinct().all()

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
            self.output_generation_log = "Generation failed. Input wasn't generated"
            self.output_generation_successful = False
        else:
            solution = self.solution
            if solution is None:
                self.output_generation_log = "Generation failed. No model solution specified."
                self.output_generation_successful = False
            else:
                problem_code = self.problem.get_judge_code()
                testcase_code = self.get_judge_code()
                judge = self.problem.get_judge()
                task_type = self.problem.get_task_type()
                if solution.language not in judge.get_supported_languages():
                    self.output_generation_log = \
                        "Generation failed. Solution language is not supported by the judge"
                    self.output_generation_successful = False
                else:
                    evaluation_result = task_type.generate_output(
                        problem_code=problem_code,
                        testcase_code=testcase_code,
                        language=solution.language,
                        solution_file=(solution.name, solution.code),
                    )
                    if not evaluation_result.success:
                        self.output_generation_log = \
                            "Generation failed. Judge couldn't execute the solution. Details: {}".format(
                                evaluation_result.message
                            )
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
        if not self.generation_started():
            self.input_generation_task_id = TestCaseInputGeneration().delay(self).id
            self.save()

    @property
    def output_file(self):
        """
        returns a File instance for the input file or None if the input hasn't been generated yet.
        If the latter is the case, then it automatically starts the generation of input file.
        """
        if not self.output_file_generated():
            return None
        if self.output_static is False:
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
        self.output_generation_task_id = None
        if commit:
            self.save()

    def _invalidate_input(self, commit=True):
        self.input_generation_log = None
        self._input_generated_file = None
        self.input_generation_successful = None
        self.input_generation_task_id = None
        if commit:
            self.save()

    def _invalidate_validation(self):
        self.validation_results.all().delete()

    def invalidate(self):
        self._invalidate_output(commit=False)
        self._invalidate_validation()
        self._invalidate_input(commit=False)
        self.judge_initialization_successful = None
        self.judge_initialization_task_id = None
        self.save()

    def has_errors(self):
        # FIXME: Actually check for errors
        return False
        input_generation_failed = not self.input_file_generated()
        output_generation_failed = not self.output_file_generated()
        input_validation_failed = not self.input_file_validated()

        failed = \
            input_generation_failed or \
            output_generation_failed or \
            input_validation_failed

        return failed

    def input_generation_completed(self):
        return self.input_static or self.input_generation_successful is not None

    def output_generation_completed(self):
        return self.output_static or self.output_generation_successful is not None

    def testcase_generation_completed(self):
        # FIXME: Actually check for generation status
        return True

        if self.input_generation_successful is False:
            return True

        input_validation_tried = \
            self.validation_results.filter(valid__isnull=False).count() == len(self.validators)

        return self.input_generation_completed() and \
               self.output_generation_completed() and \
               input_validation_tried

    def generation_started(self):
        return self.input_generation_task_id is not None

    def being_generated(self):
        return (not self.testcase_generation_completed()) and self.generation_started()

    def __str__(self):
        return self.name


class Subtask(JSONModel):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), related_name="subtasks", default=0)
    name = models.CharField(max_length=100, verbose_name=_("name"), db_index=True, primary_key=True)
    score = models.IntegerField(verbose_name=_("score"))
    testcases = GitToGitManyToManyField(TestCase, verbose_name=_("testcases"), related_name="+", blank=True)
    validators = GitToGitManyToManyField(Validator, verbose_name=_("validators"), related_name="subtasks", blank=True)
    index = models.IntegerField(verbose_name=_("index"))

    class Meta:
        ordering = ("index",)
        unique_together = ("problem", "name",)
        index_together = ("problem", "name",)
        json_db_name = "subtasks.json"
        storage_name = "subtasks"

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def get_value_as_dict(self):
        data = {
            "score": str(self.score),
            "testcases": ",".join([str(testcase) for testcase in self.testcases.all()])
        }
        return data

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        model = cls
        if model._meta.json_db_name is not None:
            try:
                raw_data = transaction.get_blob([model._meta.json_db_name]).decode('utf-8')
                pks = json.loads(raw_data)["subtasks"].keys()
            except GitError:
                logger.warning("{} not found".format(model._meta.json_db_name))
                pks = list()
            except (ValueError, UnicodeError) as e:
                raise model.InvalidObject(e)
        else:
            raise ValueError("json_db_name should be set in model's meta")

        return pks

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = cls(pk=pk)
        obj._transaction = transaction
        try:
            raw_data = transaction.get_blob(obj.path).decode('utf-8')
            full_data = json.loads(raw_data)
            content = full_data["subtasks"][pk]
        except KeyError:
            raise cls.DoesNotExist(
                'object with pk {} does not exist'.format(pk))
        except ValueError as e:
            raise cls.InvalidObject(e)
        if "global_validators" in full_data:
            content["validators"] += full_data["global_validators"]
        mapping_file = os.path.join(obj.problem.get_storage_path(), "tests", "mapping")
        if os.path.exists(mapping_file):
            testcases = []
            with open(mapping_file, "r") as file_:
                for line in file_.readlines():
                    try:
                        data = line.strip().split(' ')
                        subtask_name, testcase_name = data[0], data[1]
                        if subtask_name == obj.name:
                            testcases.append(testcase_name)
                    except Exception:
                        pass
            content["testcases"] = testcases
        obj.load(content)
        return obj

    def __str__(self):
        return self.name

    def clone_relations(self, cloned_instances, ignored_instances):
        if self in ignored_instances:
            return
        testcases = []
        for testcase in self.testcases.all():
            if testcase in cloned_instances:
                testcases.append(cloned_instances[testcase])
        cloned_instances[self].testcases.clear()
        if len(testcases) > 0:
            cloned_instances[self].testcases.add(*testcases)
