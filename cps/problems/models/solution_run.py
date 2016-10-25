# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from judge import Judge
from judge.results import JudgeVerdict
from problems.models import Solution, RevisionObject
from problems.models.testdata import TestCase
from problems.models.problem import ProblemRevision
from problems.utils import run_checker
from runner.decorators import allow_async_method


__all__ = ["SolutionRun", "SolutionRunResult"]


class SolutionRun(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem revision"))
    solutions = models.ManyToManyField(Solution, verbose_name=_("solution"))
    testcases = models.ManyToManyField(TestCase, verbose_name=_("testcases"))
    creation_date = models.DateTimeField(auto_now_add=True, verbose_name=_("creation date"))

    def run(self):
        for solution in self.solutions.all():
            for testcase in self.testcases.all():
                result = SolutionRunResult(solution_run=self, solution=solution, testcase=testcase)
                result.save()
                result.evaluate.async()

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

    _VERDICTS = [(x.name, x.value) for x in list(JudgeVerdict)]

    solution_run = models.ForeignKey(SolutionRun, verbose_name=_("solution run"), editable=False,
                                     related_name="results")
    solution = models.ForeignKey(Solution, verbose_name=_("solution"), editable=False)
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"), editable=False)

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
    solution_exit_code = models.CharField(verbose_name=_("solution exit code"), max_length=100, null=True)
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
    checker_exit_code = models.CharField(verbose_name=_("checker exit code"), max_length=100, null=True)
    checker_execution_success = models.NullBooleanField(verbose_name=_("checker execution success"), null=True)

    @allow_async_method
    def evaluate(self):
        problem = self.solution_run.problem
        problem_code = problem.get_judge_code()
        testcase_code = self.testcase.get_judge_code()
        judge = Judge.get_judge()
        evaluation_result = judge.generate_output(
            problem_code,
            self.solution.code.source_language,
            [(self.solution.code.name, self.solution.code.source_file)],
            testcase_code
        )
        self.solution_output, self.solution_execution_success, \
            self.solution_execution_time, self.solution_memory_usage, self.solution_exit_code, \
            self.verdict, \
            self.solution_execution_message = \
            evaluation_result.output_file, \
            evaluation_result.success, \
            evaluation_result.execution_time, \
            evaluation_result.execution_memory, \
            evaluation_result.exit_code, \
            evaluation_result.verdict.name, \
            evaluation_result.message

        self.save()

        if self.verdict == JudgeVerdict.ok.name:
            self.checker_execution_success, self.checker_exit_code, \
                self.score, self.checker_contestant_comment,\
                self.checker_standard_output, \
                self.checker_standard_error = run_checker(
                    self.solution_run.problem.problem_data.checker,
                    input_file=self.testcase.input_file,
                    jury_output=self.testcase.output_file,
                    contestant_output=self.solution_output
                )
        else:
            self.score = 0

        self.save()
