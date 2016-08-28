# Amirmohsen Ahanchi

from typing import List, Tuple
from unittest.case import skip

import os
import tempfile
from django.core.files import File
from django.core.files.base import ContentFile
from django.test import TestCase

# Create your tests here.
from operator import contains

from file_repository.models import FileModel
from runner import create_sandbox
from runner.models import JobModel, JobFile
from runner.sandbox.sandbox import SandboxBase


def put_files(files) -> List[FileModel]:
    fms = []
    for name, text in files:
        with tempfile.TemporaryFile(mode="w+") as tf:
            tf.write(text)
            fm = FileModel(file=File(file=tf, name=name))
            fm.save()
            fms += [fm]
    return fms


# TODO: remove redundant tests
class RunnerTest(TestCase):
    def test_sandbox_create(self):
        create_sandbox()

    def test_touch_file(self):
        filename = "touch.txt"
        job = JobModel(command=["/bin/touch", filename])
        job.save()

        job.add_file(None, JobFile.WRITABLE, "touch.txt")
        job.mark_file_for_extraction(filename)

        # should not throw JobException
        job.run()
        self.assertEqual(job.exit_status, SandboxBase.EXIT_OK)
        self.assertEqual(job.exit_code, 0)

    @skip
    def test_sandbox_file(self):
        names = ["a", "b", "c"]
        files = [(name + ".txt", name) for name in names]
        fms = put_files(files)

        job = JobModel(command=["/bin/ls"], stdout_filename="output.txt")
        job.save()
        for fm in fms:
            job.add_file(fm, JobFile.READONLY)
        job.mark_file_for_extraction("output.txt")

        job.run()

        output = job.get_extracted_file("output.txt")
        out = output.file.read().decode("utf-8")
        for fm in fms:
            filename = os.path.basename(fm.file.name)
            self.assertIn(filename, out)

    def test_execution_time(self):
        job = JobModel(command=["/bin/sleep", "0.5"])
        job.save()
        job.run()
        self.assertAlmostEqual(job.execution_wall_clock_time, 0.5, places=1)

    TEST_CODE = '#include <iostream>\n' \
                'using namespace std;\n' \
                'int main()\n' \
                '{for (int i = 0; i < 100000000; i++);' \
                'int x;\n' \
                'cin >> x;\n' \
                'cout << "Winter is coming" << endl << x << endl; return 0;}'

    def test_compile(self):
        source = FileModel(file=ContentFile(self.TEST_CODE, name="code.cpp"))
        source.save()

        job = JobModel(command=["/usr/bin/g++", "code.cpp", "-o", "a.out"], compile_job=True)
        job.save()

        job.add_file(source, JobFile.READONLY, "code.cpp")
        job.mark_file_for_extraction("a.out")

        job.run()
        self.assertEqual(job.exit_status, SandboxBase.EXIT_OK)
        self.assertEqual(job.exit_code, 0)
        return job

    def test_compile_and_execute(self):
        job_compile = self.test_compile()
        executable = job_compile.get_extracted_file("a.out")

        job_execute = JobModel(command=["./a.out"], stdin_filename="input.txt", stdout_filename="output.txt")
        job_execute.save()

        job_execute.add_file(executable, JobFile.EXECUTABLE, "a.out")
        job_execute.add_file(put_files([("input.txt", "85")])[0], JobFile.READONLY, "input.txt")
        # create empty output file
        job_execute.add_file(type=JobFile.WRITABLE, filename="output.txt")
        job_execute.mark_file_for_extraction("output.txt")

        job_execute.run()

        self.assertEqual(job_execute.exit_status, SandboxBase.EXIT_OK)
        self.assertEqual(job_execute.exit_code, 0)
        output = job_execute.get_extracted_file("output.txt")
        self.assertEqual(output.file.read(), b"Winter is coming\n85\n")
