import tempfile

from django.core.files import File

from model_mommy import mommy
import problems
from problems.models import SourceFile, ProblemData, ProblemRevision, TestCase, Solution, InputGenerator
import mock as mock
from django.test import TestCase as UnitTestCase
from .utils import get_resource_as_file_model, create_mommy_valid_testcase

from file_repository.models import FileModel


class TestCaseTests(UnitTestCase):

    def setUp(self):
        problem = mommy.make(ProblemRevision)
        solution = Solution.objects.create(
            problem=problem,
            code=get_resource_as_file_model("codes", "print_bye_world.cpp"),
            language="c++",
        )
        ProblemData.objects.create(
            problem=problem,
            time_limit=2,
            memory_limit=64,
            task_type="Batch",
            model_solution=solution
        )
        generator = InputGenerator.objects.create(
            problem=problem,
            source_file=get_resource_as_file_model("codes", "print_arguments.cpp"),
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
        output = self.testcase.output_file.file
        self.assertIsNotNone(output)
        self.assertEqual(output.readline().decode().strip(), "Bye World")
