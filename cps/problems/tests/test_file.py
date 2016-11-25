import hashlib
import os
import stat
import shutil
import tempfile

from django.core.files import File

from model_mommy import mommy
import mock as mock
from django.test import TestCase

from file_repository.models import FileModel
from problems.models import Checker, SourceFile
from .utils import get_resource_as_file_model
import subprocess


class SourceFileTests(TestCase):

    def test_successful_compile(self):
        source_file = mommy.make(Checker,
                                 name="print_hello_world.cpp",
                                 source_language="c++",
                                 source_file=get_resource_as_file_model("codes", "print_hello_world.cpp"))
        source_file.compile()
        self.assertIsNotNone(source_file._compiled_file)
        with tempfile.TemporaryDirectory() as temp_dir:
            exec_path = os.path.join(temp_dir, "executable")
            shutil.copy(source_file.compiled_file().file.path, exec_path)
            os.chmod(exec_path, stat.S_IREAD | stat.S_IEXEC)
            execution_output = subprocess.check_output([exec_path])
            self.assertEqual("Hello World", execution_output.decode().strip())


    def test_compilation_error(self):
        source_file = mommy.make(Checker,
                                 name="print_hello_world.cpp",
                                 source_language="c++",
                                 source_file=get_resource_as_file_model("codes", "compilation_error.cpp"))
        source_file.compile()
        self.assertIsNone(source_file._compiled_file)

    def test_auto_naming_containing_good_characters(self):
        file_model = get_resource_as_file_model("codes", "print_hello_world.cpp")
        file_model.name = "%%%print_hello_%%%world.cpp%%%"
        file_model.save()
        source_file = mommy.make(Checker,
                                 name="",
                                 source_language="c++",
                                 source_file=file_model)
        self.assertEqual(source_file.name, "print_hello_world.cpp")

    def test_auto_naming_with_no_good_characters(self):
        file_model = get_resource_as_file_model("codes", "print_hello_world.cpp")
        file_model.name = "%%%"
        file_model.save()
        source_file = mommy.make(Checker,
                                 name="",
                                 source_language="c++",
                                 source_file=file_model)
        self.assertEqual(source_file.name, hashlib.md5("print_hello_world.cpp"))