import os
import tempfile

from django.core.files import File

from model_mommy import mommy
import mock as mock
from django.test import TestCase

from file_repository.models import FileModel
from problems.models import SourceFile
from runner.models import JobFile


class SourceFileTests(TestCase):
    @mock.patch(target='problems.models.file.get_compilation_command', return_value="A")
    @mock.patch(target='problems.models.file.JobModel')
    def test_name_of_compiled_file(self, mock_job_model, mock_get_compilation_command):
        file1 = tempfile.NamedTemporaryFile()
        file_model1 = FileModel(file=File(file1), name="keyvan")
        file_model1.save()
        job_file = JobFile(file_model=file_model1)
        mock_job_model.return_value.mark_file_for_extraction.return_value = job_file
        file = tempfile.NamedTemporaryFile()
        file_model = FileModel(file=File(file), name="mohammad")
        file_model.save()
        source_file = mommy.make(SourceFile, source_file=file_model)
        source_file.compile()
        self.assertEqual(source_file.compiled_file().name, "keyvan")

    def test_compile(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'codes', 'empty.cpp')
        file = open(file_path, 'r')
        file_model = FileModel(file=File(file), name="code")
        file_model.save()
        source_file = mommy.make(SourceFile, source_language="c++", source_file=file_model)
        source_file.compile()