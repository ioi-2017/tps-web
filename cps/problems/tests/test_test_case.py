import tempfile

from django.core.files import File

from model_mommy import mommy
import problems
from problems.models import SourceFile, ProblemRevision, TestCase, Solution, InputGenerator
from problems.models.problem_data import ProblemData
import mock as mock
from django.test import TestCase as UnitTestCase

from problems.models.enums import SolutionVerdict
from .utils import get_resource_as_file_model, create_mommy_valid_testcase

from file_repository.models import FileModel


class TestCaseTests(UnitTestCase):

    def setUp(self):
        problem = mommy.make(ProblemRevision)
        solution = Solution.objects.create(
            problem=problem,
            code=get_resource_as_file_model("codes", "print_bye_world.cpp"),
            language="c++",
            verdict=SolutionVerdict.model_solution.name
        )
        ProblemData.objects.create(
            problem=problem,
            time_limit=2,
            memory_limit=64,
            task_type="Batch",
        )
        generator = InputGenerator.objects.create(
            problem=problem,
            file=get_resource_as_file_model("codes", "print_arguments.cpp"),
            source_language="c++",
        )
        self.testcase = create_mommy_valid_testcase(
            problem=problem,
            input_generator_name=generator.name,
            input_generator_parameters="Hello World",
            static_output=False
        )

    def test_input_generation(self):
        input = self.testcase.input_file.file
        self.assertIsNotNone(input)
        self.assertEqual(input.readline().decode().strip(), "Hello World")

    def test_output_generation(self):

        output = self.testcase.output_file
        self.assertIsNotNone(output, self.testcase._output_generation_log)
        self.assertEqual(output.file.readline().decode().strip(), "Bye World")
