# Amir Keivan Mohtashami
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models.enums import SolutionVerdict
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
    _VERDICTS = [(x.name, x.value) for x in list(JudgeVerdict)]

    solution_run = models.ForeignKey(SolutionRun, verbose_name=_("solution run"), editable=False,
                                     related_name="results")
    solution = models.ForeignKey(Solution, verbose_name=_("solution"), editable=False)
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"), editable=False)

    class Meta:
        unique_together = ("solution_run", "solution", "testcase")

    verdict = models.CharField(
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

    def run(self):
        problem = self.solution_run.problem
        # FIXME: Handle the case in which the judge code can't be acquired
        problem_code = problem.get_judge_code()
        testcase_code = self.testcase.get_judge_code()
        judge = Judge.get_judge()
        if self.solution.language not in judge.get_supported_languages():
            self.verdict = JudgeVerdict.invalid_submission.name
            self.save()
            return

        evaluation_result = judge.generate_output(
            problem_code,
            self.solution.language,
            [(self.solution.name, self.solution.code)],
            testcase_code
        )
        self.solution_output, self.solution_execution_success, \
        self.solution_execution_time, self.solution_memory_usage, \
        self.verdict, \
        self.solution_execution_message = \
            evaluation_result.output_file, \
            evaluation_result.success, \
            evaluation_result.execution_time, \
            evaluation_result.execution_memory, \
            evaluation_result.verdict.name, \
            evaluation_result.message

        self.save()

        if self.verdict == JudgeVerdict.ok.name:
            self.checker_execution_success, \
            self.score, self.contestant_message, \
            self.checker_standard_output, \
            self.checker_standard_error, \
            self.checker_execution_message = run_checker(
                self.solution_run.problem.problem_data.checker,
                input_file=self.testcase.input_file,
                jury_output=self.testcase.output_file,
                contestant_output=self.solution_output
            )
        else:
            self.score = 0

        self.save()

    def validate(self, strict=False):
        if self.checker_execution_success is not True:
            return False
        if not strict and (self.verdict == JudgeVerdict.ok.name and self.score == 1):
            return True
        if self.solution.verdict in [SolutionVerdict.correct.name, SolutionVerdict.model_solution.name]:
            return self.verdict == JudgeVerdict.ok.name and self.score == 1
        elif self.solution.verdict == SolutionVerdict.incorrect.name:
            return self.verdict == JudgeVerdict.ok.name and self.score == 0
        elif self.solution.verdict == SolutionVerdict.runtime_error.name:
            return self.verdict == JudgeVerdict.runtime_error.name
        elif self.solution.verdict == SolutionVerdict.memory_limit.name:
            return self.verdict == JudgeVerdict.memory_limit_exceeded.name
        elif self.solution.verdict == SolutionVerdict.time_limit.name:
            return self.verdict == JudgeVerdict.time_limit_exceeded.name
        elif self.solution.verdict == SolutionVerdict.failed.name:
            return self.verdict != JudgeVerdict.ok.name or self.score != 1
        elif self.solution.verdict == SolutionVerdict.time_limit_and_runtime_error.name:
            return self.verdict == JudgeVerdict.runtime_error.name or self.verdict == JudgeVerdict.time_limit_exceeded.name
        return False

    def get_short_name_for_verdict(self):
        if self.verdict == JudgeVerdict.ok.name:
            if self.checker_execution_success is None:
                return "N / A"
            elif self.checker_execution_success:
                if self.score == 1:
                    return "AC"
                elif self.score == 0:
                    return "WA"
                else:
                    return self.score
            else:
                return "Failed"
        elif self.verdict is None:
            return "N / A"
        elif self.verdict == JudgeVerdict.memory_limit_exceeded.name:
            return "ML"
        elif self.verdict == JudgeVerdict.time_limit_exceeded.name:
            return "TL"
        else:
            return "RE"
