import tempfile

from django.core.files import File

from model_mommy import mommy
import problems
from problems.models import SourceFile, ProblemData, ProblemRevision
import mock as mock
from django.test import TestCase

from file_repository.models import FileModel
from runner.models import JobFile


class TestCaseTests(TestCase):
    @mock.patch(target='problems.models.testdata.SourceFile.compiled_file')
    @mock.patch(target='problems.models.testdata.get_execution_command', return_value=["A"])
    @mock.patch(target='problems.models.testdata.JobModel')
    def test_name_of_non_static_input_file(self, mock_job_model, mock_get_executation_command,
                                           mock_source_file_compiled_file):
        file = tempfile.NamedTemporaryFile()
        file_model = FileModel(file=File(file), name="input.txt")
        file_model.save()
        job_file = JobFile(file_model=file_model)
        mock_job_model.return_value.mark_file_for_extraction.return_value = job_file
        test_case = mommy.make(problems.models.testdata.TestCase, _input_static=False,
                               _input_generator=mommy.make(problems.models.file.SourceFile),
                               _input_generation_parameters="A")
        self.assertFalse(test_case.input_file_generated())
        test_case.generate_input_file()
        self.assertEqual(test_case.input_file.name, "input.txt")
        self.assertTrue(test_case.input_file_generated())

    def test_generate_input_for_static_input_file(self):
        test_case = mommy.make(problems.models.testdata.TestCase, _input_static=True,
                               _input_uploaded_file=mommy.make(FileModel))
        self.assertRaises(AssertionError, test_case.generate_input_file)
        self.assertTrue(test_case.input_file_generated())

    def test_generate_input_for_testcase_without_generator(self):
        test_case = mommy.make(problems.models.testdata.TestCase, _input_static=False,
                               _input_generator=None,
                               _input_generation_parameters="A")
        self.assertRaises(AssertionError, test_case.generate_input_file)
        self.assertFalse(test_case.input_file_generated())

    def test_get_input_file_with_uploaded_input_file(self):
        file = tempfile.NamedTemporaryFile()
        file_model = FileModel(file=File(file), name="input.txt")
        file_model.save()
        test_case = mommy.make(problems.models.testdata.TestCase, _input_static=True,
                               _input_uploaded_file=file_model)
        self.assertEqual(test_case.input_file.name, "input.txt")
        self.assertTrue(test_case.input_file_generated())

    @mock.patch(target='problems.models.testdata.SourceFile.compiled_file')
    @mock.patch(target='problems.models.testdata.get_execution_command', return_value=["A"])
    @mock.patch(target='problems.models.testdata.JobModel')
    def test_name_of_non_static_output_file(self, mock_job_model, mock_get_executation_command,
                                            mock_source_file_compiled_file):
        file = tempfile.NamedTemporaryFile()
        file_model = FileModel(file=File(file), name="output.txt")
        file_model.save()
        job_file = JobFile(file_model=file_model)
        mock_job_model.return_value.mark_file_for_extraction.return_value = job_file
        problem_revision = mommy.make(ProblemRevision)
        problem_data = mommy.make(ProblemData, problem=problem_revision)
        test_case = mommy.make(problems.models.testdata.TestCase, problem=problem_revision, _output_static=False,
                               _solution=mommy.make(problems.models.file.SourceFile),
                               _input_generator=mommy.make(problems.models.file.SourceFile),
                               _input_generation_parameters="A")
        self.assertFalse(test_case.output_file_generated())
        test_case.generate_output_file()
        self.assertEqual(test_case.output_file.name, "output.txt")
        self.assertTrue(test_case.output_file_generated())

    def test_generate_output_for_static_output_file(self):
        test_case = mommy.make(problems.models.testdata.TestCase, _output_static=True,
                               _output_uploaded_file=mommy.make(FileModel),
                               _input_generator=mommy.make(problems.models.file.SourceFile),
                               _input_generation_parameters="A")
        self.assertRaises(AssertionError, test_case.generate_output_file)
        self.assertTrue(test_case.output_file_generated())

    def test_generate_output_for_testcase_without_solution(self):
        test_case = mommy.make(problems.models.testdata.TestCase, _output_static=False,
                               _solution=None,
                               _input_generator=mommy.make(problems.models.file.SourceFile),
                               _input_generation_parameters="A")
        self.assertRaises(AssertionError, test_case.generate_output_file)
        self.assertFalse(test_case.output_file_generated())

    def test_get_output_file_with_uploaded_output_file(self):
        file = tempfile.NamedTemporaryFile()
        file_model = FileModel(file=File(file), name="output.txt")
        file_model.save()
        test_case = mommy.make(problems.models.testdata.TestCase, _output_static=True,
                               _output_uploaded_file=file_model,
                               _input_generator=mommy.make(problems.models.file.SourceFile),
                               _input_generation_parameters="A")
        self.assertEqual(test_case.output_file.name, "output.txt")
        self.assertTrue(test_case.output_file_generated())
