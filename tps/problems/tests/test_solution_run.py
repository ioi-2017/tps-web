import tempfile

from celery import Task
from celery.contrib.methods import task_method
from django.core.files import File

from model_mommy import mommy
import mock as mock
from django.test import TestCase as UnitTestCase

from judge.results import JudgeVerdict
from .utils import get_resource_as_file_model, create_mommy_valid_testcase

from file_repository.models import FileModel
from problems.models import ProblemRevision, SolutionRun, Solution, TestCase, Checker
from problems.models.problem_data import ProblemData


class SolutionRunMockedTests(UnitTestCase):
    def test_creation_and_run(self):
        def false_evaluation(obj):
            obj.score = 10
            obj.save()
        with mock.patch(
            target='problems.models.solution_run.SolutionRunResult.run',
            new=false_evaluation
        ) as evalutate_patch:
            problem_revision = mommy.make(ProblemRevision)
            solutions = []
            solutions.append(mommy.make(Solution, name="S1" , problem=problem_revision))
            solutions.append(mommy.make(Solution, name="S2", problem=problem_revision))
            testcases = mommy.make(TestCase, _quantity=2, problem=problem_revision,
                                   _input_static=True,
                                   _input_uploaded_file=mommy.make(FileModel),
                                   _output_static=True,
                                   _output_uploaded_file=mommy.make(FileModel),
            )
            solution_run = SolutionRun.create(solutions, testcases)

            self.assertEqual(solution_run.testcases.all().count(), 2)
            self.assertEqual(solution_run.solutions.all().count(), 2)

            solution_run.run()

            self.assertEqual(solution_run.results.all().count(), 4)

            for result in solution_run.results.all():
                self.assertEqual(result.score, 10)


class SolutionRunFunctionalTests(UnitTestCase):

    def setUp(self):
        self.problem = mommy.make(ProblemRevision)
        self.hello_solution = Solution.objects.create(
            problem=self.problem,
            name="hello_world.cpp",
            code=get_resource_as_file_model("codes", "print_hello_world.cpp"),
            language="c++"
        )
        self.bye_solution = Solution.objects.create(
            problem=self.problem,
            name="bye_world.cpp",
            code=get_resource_as_file_model("codes", "print_bye_world.cpp"),
            language="c++"
        )

        self.no_solution = Solution.objects.create(
            problem=self.problem,
            name="no_world.cpp",
            code=get_resource_as_file_model("codes", "print_no_world.cpp"),
            language="c++"
        )

        self.runtime_error_solution = Solution.objects.create(
            problem=self.problem,
            name="runtime_error.cpp",
            code=get_resource_as_file_model("codes", "runtime_error.cpp"),
            language="c++"
        )

        self.time_limit_solution =  Solution.objects.create(
            problem=self.problem,
            name="time_limit.cpp",
            code=get_resource_as_file_model("codes", "time_limit.cpp"),
            language="c++"
        )

        self.not_compilable_solution = Solution.objects.create(
            problem=self.problem,
            name="compilation_error.cpp",
            code=get_resource_as_file_model("codes", "compilation_error.cpp"),
            language="c++"
        )

        self.testcase_different_output = create_mommy_valid_testcase(
            problem=self.problem,
            input_static_file=get_resource_as_file_model("statics", "hello_world.txt"),
            output_static_file=get_resource_as_file_model("statics", "bye_world.txt"),
        )

        self.testcase_same_output = create_mommy_valid_testcase(
            problem=self.problem,
            input_static_file=get_resource_as_file_model("statics", "hello_world.txt"),
            output_static_file=get_resource_as_file_model("statics", "hello_world.txt"),
        )

        self.checker = Checker.objects.create(
            problem=self.problem,
            file=get_resource_as_file_model("codes", "checker_first_line_equal.cpp"),
            source_language="c++",
        )

        problem_data = ProblemData.objects.create(
            problem=self.problem,
            task_type="Batch",
            time_limit=0.5,
            memory_limit=64,
            checker=self.checker,
        )

        self.solutions = [self.hello_solution, self.bye_solution, self.no_solution,
                          self.time_limit_solution, self.runtime_error_solution, self.not_compilable_solution]
        self.testcases = [self.testcase_different_output, self.testcase_same_output]

        solution_run = SolutionRun.create(
            solutions=self.solutions,
            testcases=self.testcases,
        )

        solution_run.run()

        self.results = {}

        for solution in self.solutions:
            self.results[solution] = {}
            for testcase in self.testcases:
                self.results[solution][testcase] = solution_run.results.get(
                    solution=solution,
                    testcase=testcase
                )

    def assertVerdictAndScore(self, solution, testcase, verdict, score=None, contestant_message=None):
        result = self.results[solution][testcase]
        self.assertEqual(result.verdict, verdict.name)
        if verdict == JudgeVerdict.ok:
            self.assertEqual(result.score, score)
            if contestant_message:
                self.assertTrue(contestant_message in result.contestant_message)

    def test_runtime_error_solution(self):
        for testcase in self.testcases:
            self.assertVerdictAndScore(self.runtime_error_solution, testcase, JudgeVerdict.runtime_error)

    def test_time_limit_solution(self):
        for testcase in self.testcases:
            self.assertVerdictAndScore(self.time_limit_solution, testcase, JudgeVerdict.time_limit_exceeded)

    def test_problem_in_checker(self):
        testcase = self.testcase_different_output
        solution = self.no_solution
        self.assertVerdictAndScore(solution, testcase, JudgeVerdict.ok, None)
        result = self.results[solution][testcase]
        self.assertFalse(result.checker_execution_success)
        self.assertTrue("First" in result.checker_execution_message)

    def test_zero_score(self):
        testcase = self.testcase_same_output
        for solution in [self.hello_solution, self.bye_solution, self.no_solution]:
            self.assertVerdictAndScore(solution, testcase, JudgeVerdict.ok, 0, "Judge")

    def test_full_score(self):
        testcase = self.testcase_different_output
        self.assertVerdictAndScore(self.bye_solution, testcase, JudgeVerdict.ok, 1, "Correct")

    def test_half_score(self):
        testcase = self.testcase_different_output
        self.assertVerdictAndScore(self.hello_solution, testcase, JudgeVerdict.ok, 0.5, "doesn't match")

    def test_compilation_error(self):
        for testcase in self.testcases:
            self.assertVerdictAndScore(
                self.not_compilable_solution,
                testcase,
                JudgeVerdict.compilation_failed,
                0.5,
                "doesn't match"
            )



