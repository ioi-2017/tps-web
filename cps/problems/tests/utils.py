from django.core.files import File
from model_mommy import mommy

from problems.models import *
import os
from file_repository.models import FileModel

__all__ = ["get_resource_as_file_model", "create_mommy_valid_testcase"]

def get_resource_as_file_model(*path):

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, *path)
    file = open(file_path, 'r')
    file_model = FileModel(file=File(file))
    file_model.save()
    return file_model

def create_mommy_valid_testcase(problem=None,
                                input_generator_name=None, input_generator_parameters="",
                                input_static_file=None,
                                static_output=True, output_static_file=None,
                                **additional_data):
    testcase_data = additional_data.copy()

    if problem:
        testcase_data["problem"] = problem

    static_input = input_generator_name is None
    testcase_data["_input_static"] = static_input
    if static_input:
        if input_static_file:
            testcase_data["_input_uploaded_file"] = input_static_file
        else:
            testcase_data["_input_uploaded_file"] = get_resource_as_file_model("statics", "hello_world.txt")
    else:
        testcase_data["_input_generator_name"] = input_generator_name
        testcase_data["_input_generation_parameters"] = input_generator_parameters

    testcase_data["_output_static"] = static_output
    if static_output:
        if output_static_file:
            testcase_data["_output_uploaded_file"] = output_static_file
        else:
            testcase_data["_output_uploaded_file"] = get_resource_as_file_model("statics", "hello_world.txt")

    return mommy.make(TestCase, **testcase_data)


