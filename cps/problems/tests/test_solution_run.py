import tempfile

from celery import Task
from celery.contrib.methods import task_method
from django.core.files import File

from model_mommy import mommy
import mock as mock
from django.test import TestCase as UnitTestCase

from file_repository.models import FileModel
from problems.models import ProblemRevision, SolutionRun, Solution, TestCase


class SolutionRunTests(UnitTestCase):
    def test_creation_and_run(self):
        def false_evaluation(obj):
            obj.score = 10
            obj.save()
        with mock.patch(
            target='problems.models.solution_run.SolutionRunResult.run',
            new=false_evaluation
        ) as evalutate_patch:
            problem_revision = mommy.make(ProblemRevision)
            solutions = mommy.make(Solution, _quantity=2, problem=problem_revision)
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




