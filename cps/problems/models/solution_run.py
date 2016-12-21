# Amir Keivan Mohtashami
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models.enums import SolutionVerdict, SolutionRunVerdict
from tasks.models import Task
from file_repository.models import FileModel
from judge import Judge
from judge.results import JudgeVerdict
from problems.models import Solution, RevisionObject
from problems.models.problem import ProblemRevision
from problems.models.testdata import TestCase
from problems.utils import run_checker
from tasks.decorators import allow_async_method

__all__ = ["SolutionRun", "SolutionRunResult"]


class SolutionRun(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem revision"))
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
                result.apply_async()

    @staticmethod
    def get_matching_fields():
        return ["pk"]

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


class SolutionRunResult(Task):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionRunVerdict)]

    solution_run = models.ForeignKey(SolutionRun, verbose_name=_("solution run"), editable=False,
                                     related_name="results")
    solution = models.ForeignKey(Solution, verbose_name=_("solution"), editable=False)
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"), editable=False)

    class Meta:
        unique_together = ("solution_run", "solution", "testcase")

    solution_verdict = models.CharField(
        max_length=max([len(x[0]) for x in _VERDICTS]),
        verbose_name=_("verdict"),
        choices=_VERDICTS,
        null=True
    )
    score = models.FloatField(verbose_name=_("score"), null=True)
    contestant_message = models.TextField(verbose_name=_("checker comment to contestant"), null=True)

    solution_output = models.ForeignKey(FileModel, verbose_name=_("solution output file"), null=True, related_name='+')
    solution_execution_time = models.FloatField(verbose_name=_("solution execution time"), null=True)
    solution_memory_usage = models.IntegerField(verbose_name=_("solution memory usage"), null=True)
    solution_execution_success = models.NullBooleanField(verbose_name=_("solution execution success"), null=True)
    solution_execution_message = models.TextField(verbose_name=_("solution execution message"), null=True)

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
    checker_execution_success = models.NullBooleanField(verbose_name=_("checker execution success"), null=True)
    checker_execution_message = models.TextField(verbose_name=_("checker execution message"), null=True)

    @property
    def verdict(self):
        if self.solution_execution_success:
            if self.checker_execution_success is None:
                return None
            elif self.checker_execution_success is True:
                return self.solution_verdict
            else:
                return SolutionRunVerdict.checker_failed.name
        else:
            return self.solution_verdict

    def run(self):
        problem = self.solution_run.problem
        testcase = self.testcase
        # FIXME: Handle the case in which the judge code can't be acquired
        problem_code = problem.get_judge_code()
        testcase_code = testcase.get_judge_code()
        if not testcase_code:
            self.solution_verdict = SolutionRunVerdict.judge_failed
            self.solution_execution_message = _("Couldn't add testcase to the judge")
            self.save()
            return
        input_file = testcase.input_file
        if not input_file:
            self.solution_verdict = SolutionRunVerdict.invalid_testcase
            self.solution_execution_message = _("Testcase couldn't be generated")
            self.save()
            return
        # TODO: Should we check if the testcase validates as well?
        output_file = testcase.output_file
        if not output_file:
            self.solution_verdict = SolutionRunVerdict.invalid_testcase
            self.solution_execution_message = _("Testcase couldn't be generated")
            self.save()
            return

        judge = Judge.get_judge()

        evaluation_result = judge.generate_output(
            problem_code,
            self.solution.language,
            [(self.solution.name, self.solution.code)],
            testcase_code
        )
        self.solution_output, self.solution_execution_success, \
        self.solution_execution_time, self.solution_memory_usage, \
        self.solution_verdict, \
        self.solution_execution_message = \
            evaluation_result.output_file, \
            evaluation_result.success, \
            evaluation_result.execution_time, \
            evaluation_result.execution_memory, \
            evaluation_result.verdict.name, \
            evaluation_result.message

        if self.solution_output is None:
            self.solution_verdict = SolutionRunVerdict.judge_failed.name
            self.solution_execution_message = "Judge provided no output"
            self.solution_execution_success = False

        self.save()

        if self.solution_verdict == JudgeVerdict.ok.name:
            checker = self.solution_run.problem.problem_data.checker
            if checker is None:
                self.checker_execution_message = "No checker found"
                self.checker_execution_success = False
                self.save()
            else:
                self.checker_execution_success, \
                self.score, self.contestant_message, \
                self.checker_standard_output, \
                self.checker_standard_error, \
                self.checker_execution_message = run_checker(
                    self.solution_run.problem.problem_data.checker,
                    input_file=input_file,
                    jury_output=output_file,
                    contestant_output=self.solution_output
                )
        else:
            self.score = 0

        self.save()

    def validate(self, strict=False):
        if self.verdict is None:
            return True
        if self.verdict not in JudgeVerdict.__members__:
            return False
        solution_verdict = SolutionVerdict.__members__.get(self.solution.verdict)
        judge_verdict = JudgeVerdict.__members__.get(self.solution_verdict)
        if not strict and self.score == 1:
            return True
        if solution_verdict in [SolutionVerdict.correct, SolutionVerdict.model_solution]:
            return self.score == 1
        elif solution_verdict == SolutionVerdict.incorrect:
            return self.score == 0
        elif solution_verdict == SolutionVerdict.runtime_error:
            return judge_verdict == JudgeVerdict.runtime_error
        elif solution_verdict == SolutionVerdict.memory_limit:
            return judge_verdict == JudgeVerdict.memory_limit_exceeded
        elif solution_verdict == SolutionVerdict.time_limit:
            return judge_verdict == JudgeVerdict.time_limit_exceeded
        elif solution_verdict == SolutionVerdict.failed:
            return judge_verdict != JudgeVerdict.ok or self.score != 1
        elif solution_verdict == SolutionVerdict.time_limit_and_runtime_error:
            return judge_verdict in [JudgeVerdict.runtime_error, JudgeVerdict.time_limit_exceeded]
        return False

    def get_short_name_for_verdict(self):

        if self.verdict == JudgeVerdict.ok.name:
            if self.score == 1:
                return "AC"
            elif self.score == 0:
                return "WA"
            else:
                return self.score
        elif self.verdict is None:
            return "N / A"
        else:
            return SolutionRunVerdict.__members__.get(self.verdict).short_name
