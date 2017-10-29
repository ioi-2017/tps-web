import os
import shutil
import tempfile

from django.core.files import File

from file_repository.models import FileModel

__all__ = ["BaseExporter", ]


class BaseExporter(object):

    short_name = None

    def __init__(self, revision):

        self.temp_dir = tempfile.TemporaryDirectory()
        self.outer_temp_path = self.temp_dir.name
        self.path = os.path.join(self.outer_temp_path, revision.problem_data.code_name)
        self.archives_path = os.path.join(self.outer_temp_path, "archives")
        os.mkdir(self.path)
        os.mkdir(self.archives_path)

        self.revision = revision
        self.exported = False

    def _cleanup(self):
        self.temp_dir.cleanup()
        self.path = None

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        self._cleanup()

    def __del__(self):
        self._cleanup()

    def _do_export(self):
        """
            This method is responsible for exporting the revision data to
            exporter's path.
        """

        raise NotImplementedError("This must be implemented in subclasses")

    def do_export(self):
        if self.exported:
            raise ValueError("Already exported")
        self._do_export()
        self.exported = True

    def get_absolute_path(self, path):
        return os.path.join(self.path, path)

    def extract_from_storage_to_path(self, file_model, relative_path):
        if isinstance(file_model, FileModel):
            shutil.copyfile(file_model.file.path, self.get_absolute_path(relative_path))
        else:
            file_ = file_model.file
            file_.open()
            self.write_to_file(self.get_absolute_path(relative_path), file_.read())

    def extract_archive_to_storage(self, name, format="zip"):
        if not self.exported:
            raise ValueError("Export before requesting the archive")

        full_name = os.path.join(self.archives_path, name)

        archive_name = shutil.make_archive(full_name, format,
                                           root_dir=self.outer_temp_path,
                                           base_dir=self.revision.problem_data.code_name)

        archive_ = open(archive_name, "rb")

        file_model = FileModel.objects.create(
            file=File(archive_),
        )

        archive_.close()

        return file_model

    def write_to_file(self, path, content):
        absolute_path = self.get_absolute_path(path)
        if isinstance(content, str):
            file_ = open(absolute_path, "w")
        else:
            file_ = open(absolute_path, "wb")
        file_.write(content)
        file_.close()

    def create_directory(self, path):
        absolute_path = self.get_absolute_path(path)
        os.makedirs(absolute_path, exist_ok=True)
