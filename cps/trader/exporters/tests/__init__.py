import os
from tempfile import TemporaryDirectory

from django.test import TestCase
from model_mommy import mommy

from problems.models import ProblemRevision, Solution, InputGenerator, Checker, ProblemData
from problems.models.enums import SolutionVerdict
from problems.tests.utils import get_resource_as_file_model, create_mommy_valid_testcase
import shutil


class ExporterBaseTestCase(object):
    def setUp(self):
        self.problem = mommy.make(ProblemRevision)
        hello_solution = Solution.objects.create(
            problem=self.problem,
            name="hello_world.cpp",
            code=get_resource_as_file_model("codes", "print_hello_world.cpp"),
            language="c++"
        )

        time_limit_solution = Solution.objects.create(
            problem=self.problem,
            name="time_limit.cpp",
            code=get_resource_as_file_model("codes", "time_limit.cpp"),
            language="c++",
            verdict=SolutionVerdict.time_limit.name
        )

        testcase_different_output = create_mommy_valid_testcase(
            problem=self.problem,
            input_static_file=get_resource_as_file_model("statics", "hello_world.txt"),
            output_static_file=get_resource_as_file_model("statics", "bye_world.txt"),
        )

        generator = InputGenerator.objects.create(
            problem=self.problem,
            file=get_resource_as_file_model("codes", "print_arguments.cpp"),
            source_language="c++",
        )
        testcase = create_mommy_valid_testcase(
            problem=self.problem,
            input_generator_name=generator.name,
            input_generator_parameters="Hello World",
            static_output=False
        )

        checker = Checker.objects.create(
            problem=self.problem,
            name="my_tester.cpp",
            file=get_resource_as_file_model("codes", "checker_first_line_equal.cpp"),
            source_language="c++",
        )

        problem_data = ProblemData.objects.create(
            problem=self.problem,
            task_type="Batch",
            time_limit=0.5,
            memory_limit=64,
            checker=checker,
            model_solution=hello_solution
        )

    def do_export(self):
        raise NotImplementedError

    def test_exporter(self):
        file_model = self.do_export()
        with TemporaryDirectory() as tmp_dir:
            extraction_dir = os.path.join(tmp_dir, "extracted")
            os.mkdir(extraction_dir)
            archive_path = os.path.join(tmp_dir, file_model.name)
            shutil.copy(file_model.file.path, archive_path)
            shutil.unpack_archive(archive_path, extract_dir=extraction_dir)
            files_list = []
            for (dirpath, dirnames, filenames) in os.walk(extraction_dir):
                dir_rel_path = os.path.relpath(dirpath, extraction_dir)
                for filename in filenames:
                    files_list.append(os.path.join(dir_rel_path, filename))
            self.assertTrue("solutions/unknown_verdict/hello_world.cpp" in files_list)
            self.assertTrue("solutions/time_limit/time_limit.cpp" in files_list)
            self.assertTrue("./checker_my_tester.cpp" in files_list)
            # TODO: Complete the tests


