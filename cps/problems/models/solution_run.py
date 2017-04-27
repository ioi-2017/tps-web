# Amir Keivan Mohtashami
import json

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.fields import EnumField
from judge.results import JudgeVerdict
from problems.models.enums import SolutionVerdict, SolutionRunVerdict
from tasks.tasks import CeleryTask
from file_repository.models import FileModel
from judge import Judge
from problems.models import Solution, RevisionObject, SolutionSubtaskExpectedVerdict
from problems.models.testdata import TestCase
from problems.utils.run_checker import run_checker

__all__ = ["SolutionRun", "SolutionRunResult"]


class SolutionRun(RevisionObject):
    problem = models.ForeignKey("problems.ProblemRevision", verbose_name=_("problem"))
    solutions = models.ManyToManyField(Solution, verbose_name=_("solution"), related_name="+")
    testcases = models.ManyToManyField(TestCase, verbose_name=_("testcases"), related_name="+")
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_("creation date"))
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("creator"))

    def run(self):
        self.results.all().delete()
        for solution in self.solutions.all():
            for testcase in self.testcases.all():
                result = SolutionRunResult(solution_run=self, solution=solution, testcase=testcase)
                result.save()
                result.run()

    @staticmethod
    def get_matching_fields():
        return ["pk"]

    def get_value_as_dict(self):
        data = {
            "solutions": [str(solution) for solution in self.solutions.all()],
            "testcases": [str(testcase) for testcase in self.testcases.all()],
        }
        return data


    def validate(self):
        is_valid = True
        for solution in self.solutions.all():
            if not self.validate_solution(solution):
                is_valid = False
        return is_valid

    def validate_solution(self, solution):
        results = SolutionRunResult.objects.filter(solution_run=self, solution=solution)
        verdict_happend = False
        only_dont_care_happend = True
        for result in results:
            if result.validate(strict=True):
                verdict_happend = True
            if not result.validate(strict=False):
                only_dont_care_happend = False
        return verdict_happend and only_dont_care_happend

    def started(self):
        return self.results.all().count() == self.solutions.all().count() * self.testcases.all().count()

    @classmethod
    def create(cls, solutions, testcases):
        assert len(solutions) != 0, "At least one solution must exist in solution run"
        assert len(testcases) != 0, "At least one test case must exist in solution run"
        problem = solutions[0].problem
        for solution in solutions:
            assert solution.problem == problem, "All solutions and testcases must be from the same problem"
        for testcase in testcases:
            assert testcase.problem == problem, "All solutions and testcases must be from the same problem"
        solution_run = cls.objects.create(problem=problem)
        solution_run.solutions = solutions
        solution_run.testcases = testcases
        solution_run.save()
        return solution_run

    def clone(self, cloned_instances=None):
        raise NotImplementedError


# TODO: This should be removed. exceptions should be handled explicitly
def report_failed_on_exception(func):
    def wrapper(self, *args, **kwargs):
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            self.verdict = SolutionRunVerdict.judge_failed
            self.save()
            raise e
    return wrapper


class SolutionRunExecutionTask(CeleryTask):
    def validate_dependencies(self, run):
        result = True
        if run.testcase.testcase_generation_completed():
            if not run.testcase.output_generation_successful:
                run.verdict = SolutionRunVerdict.invalid_testcase
                run.execution_message = "Testcase generation failed"
                run.save()
                return False
        else:
            run.testcase.generate()
            result = None

        if run.testcase.judge_initialization_completed():
            if not run.testcase.judge_initialization_successful:
                run.verdict = SolutionRunVerdict.invalid_testcase
                run.execution_message = \
                    "Testcase couldn't be added to the judge. {}".format(
                        run.testcase.judge_initialization_message
                    )
                run.save()
                return False
        else:
            run.testcase.initialize_in_judge()
            result = None

        checker = run.testcase.problem.problem_data.checker
        if checker is None:
            run.verdict = SolutionRunVerdict.checker_failed
            run.execution_message = "Checker not found"
            run.save()
        else:
            if checker.compilation_finished:
                if not checker.compilation_successful():
                    run.verdict = SolutionRunVerdict.checker_failed
                    run.execution_message = "Checker didn't compile. Log:{}".format(checker.last_compile_log)
                    run.save()
                    return False
            else:
                checker.compile()
                result = None

        return result

    def execute(self, run):
        run._run()

class SolutionRunResult(models.Model):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionRunVerdict)]

    solution_run = models.ForeignKey(SolutionRun, verbose_name=_("solution run"), editable=False,
                                     related_name="results")
    solution = models.ForeignKey(Solution, verbose_name=_("solution"), editable=False)
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"), editable=False)

    class Meta:
        unique_together = ("solution_run", "solution", "testcase")

    verdict = EnumField(
        verbose_name=_("verdict"),
        enum=SolutionRunVerdict,
        default=SolutionRunVerdict.judging
    )
    task_id = models.CharField(verbose_name=_("task id"), max_length=128, null=True)
    execution_message = models.TextField(verbose_name=_("execution message"), null=True)
    score = models.FloatField(verbose_name=_("score"), null=True)
    contestant_message = models.TextField(verbose_name=_("checker comment to contestant"), null=True)

    solution_output = models.ForeignKey(FileModel, verbose_name=_("solution output file"), null=True, related_name='+')
    solution_execution_time = models.FloatField(verbose_name=_("solution execution time"), null=True)
    solution_memory_usage = models.IntegerField(verbose_name=_("solution memory usage"), null=True)

    checker_standard_output = models.ForeignKey(
        FileModel,
        verbose_name=_("checker standard output"),
        null=True, related_name='+'
    )
    checker_standard_error = models.ForeignKey(
        FileModel,
        verbose_name=_("checker standard error"),
        null=True, related_name='+'
    )

    @report_failed_on_exception
    def _run(self):
        problem = self.solution_run.problem
        testcase = self.testcase
        # FIXME: Handle the case in which the judge code can't be acquired
        problem_code = problem.get_judge_code()

        input_file = testcase.input_file
        if not input_file:
            self.verdict = SolutionRunVerdict.invalid_testcase
            self.execution_message = _("Testcase couldn't be generated")
            self.save()
            return
        # TODO: Should we check if the testcase validates as well?

        testcase_code = testcase.get_judge_code()
        if not testcase_code:
            self.verdict = SolutionRunVerdict.judge_failed
            self.execution_message = _("Couldn't add testcase to the judge")
            self.save()
            return

        output_file = testcase.output_file
        if not output_file:
            self.verdict = SolutionRunVerdict.invalid_testcase
            self.execution_message = _("Testcase couldn't be generated")
            self.save()
            return

        judge = Judge.get_judge()

        evaluation_result = judge.generate_output(
            problem_code,
            self.solution.language,
            [(self.solution.name, self.solution.code)],
            testcase_code
        )
        self.solution_output, solution_execution_success, \
        self.solution_execution_time, self.solution_memory_usage, \
        solution_verdict, solution_execution_message = \
            evaluation_result.output_file, \
            evaluation_result.success, \
            evaluation_result.execution_time, \
            evaluation_result.execution_memory, \
            evaluation_result.verdict, \
            evaluation_result.message

        if solution_verdict == JudgeVerdict.ok:
            if self.solution_output is None:
                self.verdict = SolutionRunVerdict.judge_failed
                self.execution_message = _("Judge provided no output")
            else:
                checker = self.solution_run.problem.problem_data.checker
                if checker is None:
                    self.verdict = SolutionRunVerdict.checker_failed
                    self.execution_message = _("No checker found")
                else:
                    checker_execution_success, \
                    self.score, self.contestant_message, \
                    self.checker_standard_output, \
                    self.checker_standard_error, \
                    checker_execution_message = run_checker(
                        self.solution_run.problem.problem_data.checker,
                        input_file=input_file,
                        jury_output=output_file,
                        contestant_output=self.solution_output
                    )
                    if checker_execution_success:
                        self.verdict = SolutionRunVerdict.ok
                    else:
                        self.verdict = SolutionRunVerdict.checker_failed
                        self.execution_message = checker_execution_message
        else:
            self.verdict = SolutionRunVerdict.get_from_judge_verdict(solution_verdict)
            self.execution_message = solution_execution_message
            self.score = 0

        self.save()

    def run(self):
        if self.task_id is None:
            self.task_id = SolutionRunExecutionTask().delay(self).id
            self.save()

    def validate(self, subtasks=None, strict=False):
        if self.verdict == SolutionRunVerdict.judging:
            return True
        if not strict and self.score == 1:
            return True
        solution_verdict = self.solution.verdict
        flag = True

        if subtasks is None:
            subtasks = self.testcase.subtasks.all()
            flag &= self.validate_for_verdict(solution_verdict)

        for subtask in subtasks:
            try:
                solution_subtask_expected_verdict = \
                    SolutionSubtaskExpectedVerdict.objects.get(
                        subtask=subtask, solution=self.solution
                    )
                flag &= self.validate_for_verdict(
                    solution_subtask_expected_verdict.verdict
                )
            except SolutionSubtaskExpectedVerdict.DoesNotExist:
                flag &= self.validate_for_verdict(solution_verdict)

        return flag

    def validate_for_verdict(self, verdict):
        judge_verdict = self.verdict
        if verdict in [SolutionVerdict.correct, SolutionVerdict.model_solution]:
            return self.score == 1
        elif verdict == SolutionVerdict.incorrect:
            return self.score == 0
        elif verdict == SolutionVerdict.runtime_error:
            return judge_verdict == SolutionRunVerdict.runtime_error
        elif verdict == SolutionVerdict.memory_limit:
            return judge_verdict == SolutionRunVerdict.memory_limit_exceeded
        elif verdict == SolutionVerdict.time_limit:
            return judge_verdict == SolutionRunVerdict.time_limit_exceeded
        elif verdict == SolutionVerdict.failed:
            return judge_verdict != SolutionRunVerdict.ok or self.score == 0
        elif verdict == SolutionVerdict.time_limit_and_runtime_error:
            return judge_verdict in [SolutionRunVerdict.runtime_error, SolutionRunVerdict.time_limit_exceeded]
        return False

    def get_short_name_for_verdict(self):
        if self.verdict == SolutionRunVerdict.ok:
            if self.score == 1:
                return "AC"
            elif self.score == 0:
                return "WA"
            else:
                return "PS: {score}".format(score=self.score)
        else:
            return self.verdict.short_name
