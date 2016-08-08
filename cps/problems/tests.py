import tempfile

import mock as mock
from django.test import TestCase

from file_repository.models import FileModel
from problems.models import SourceFile
from runner.models import JobFile, JobModel


class SourceFileTests(TestCase):
    @mock.patch(target='problems.models.file.get_compilation_command', return_value="A")
    @mock.patch(target='problems.models.file.JobModel.add_file')
    @mock.patch(target='problems.models.file.JobModel.mark_file_for_extraction')
    @mock.patch(target='problems.models.file.JobModel.run')
    @mock.patch(target='problems.models.file.SourceFile.save')
    def test_name_of_compiled_file(self, mock_source_file_save, mock_job_model_run,
                                   mock_job_model_mark_file_for_extraction, mock_job_model_add_file,
                                   mock_get_compilation_command):
        file1 = tempfile.NamedTemporaryFile()
        file_model1 = FileModel(file=file1, name="keyvan")
        job_file = JobFile(file_model=file_model1)
        mock_job_model_mark_file_for_extraction.return_value = job_file
        file = tempfile.NamedTemporaryFile()
        file_model = FileModel(file=file, name="mohammad")
        source_file = SourceFile(source_file=file_model)
        source_file.compile()
        self.assertEqual(source_file.compiled_file().name, "keyvan")
