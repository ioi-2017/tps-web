# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models import Solution
from problems.models.file import SourceFile
from problems.models.testdata import TestCase
from problems.models.problem import ProblemRevision
from problems.utils import run_with_input, run_checker
from runner.decorators import run_on_worker
from version_control.models import VersionModel

__all__ = ["SolutionRun", "SolutionRunResult"]


class SolutionRun(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem revision"))
    solutions = models.ManyToManyField(Solution, verbose_name=_("solution"))
    testcases = models.ManyToManyField(TestCase, verbose_name=_("testcases"))
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_("creation date"))

    def run(self):
        for solution in self.solutions.all():
            for testcase in self.testcases.all():
                result = SolutionRunResult(solution_run=self, solution=solution, testcase=testcase)
                result.save()
                result.evaluate()

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


class SolutionRunResult(models.Model):
    solution_run = models.ForeignKey(SolutionRun, verbose_name=_("solution run"), editable=False,
                                     related_name="results")
    solution = models.ForeignKey(Solution, verbose_name=_("solution"), editable=False)
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"), editable=False)

    score = models.FloatField(verbose_name=_("score"), null=True)
    checker_contestant_comment = models.TextField(verbose_name=_("checker comment to contestant"), null=True)
    checker_jury_comment = models.TextField(verbose_name=_("checker comment to jury"), null=True)
    output_file = models.ForeignKey(FileModel, verbose_name=_("output file"), null=True)
    execution_time = models.FloatField(verbose_name=_("execution time"), null=True)
    memory_usage = models.IntegerField(verbose_name=_("memory usage"), null=True)
    exit_code = models.CharField(verbose_name=_("exit code"), max_length=100)

    @run_on_worker
    def evaluate(self):
        problem_data = self.solution_run.problem.problem_data
        self.output_file, self.execution_time, self.memory_usage, self.exit_code = \
            run_with_input(self.solution.code,
                           input_file=self.testcase.input_file,
                           time_limit=problem_data.time_limit,
                           memory_limit=problem_data.memory_limit)
        self.score, self.checker_contestant_comment, self.checker_jury_comment = \
            run_checker(self.solution_run.problem.problem_data.checker,
                        input_file=self.testcase.input_file,
                        jury_output=self.testcase.output_file,
                        contestant_output=self.output_file
                        )
        self.save()