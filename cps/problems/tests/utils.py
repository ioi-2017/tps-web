from model_mommy import mommy

import problems
from file_repository.models import FileModel


def create_testcase_with_uploaded_files():
    test_case = mommy.make(problems.models.testdata.TestCase, _output_static=True,
                           _output_uploaded_file=mommy.make(FileModel),
                           _input_static=True,
                           _input_uploaded_file=mommy.make(FileModel))
    return test_case
