from django.test import TestCase
from mock import mock
from model_mommy import mommy

from problems.models import Validator, Subtask, ProblemRevision
from problems.tests.utils import create_mommy_valid_testcase, get_resource_as_file_model


class ValidatorTests(TestCase):
    @mock.patch(target='problems.models.validator.ValidatorResult.run')
    def test_creation_of_validator_result_with_one_subtask(self, mock_run):
        problem = mommy.make(ProblemRevision)
        subtask = mommy.make(Subtask, problem=problem)
        test_case1 = create_mommy_valid_testcase(problem=problem)
        test_case2 = create_mommy_valid_testcase(problem=problem)
        subtask.testcases.add(test_case1)
        subtask.testcases.add(test_case2)
        subtask.save()
        validator = mommy.make(Validator, global_validator=False, problem=problem)
        validator._subtasks.add(subtask)
        validator.validate()
        self.assertEqual(validator.validatorresult_set.all().count(), 2)

    @mock.patch(target='problems.models.validator.ValidatorResult.run')
    def test_creation_of_validator_result_with_many_subtasks(self, mock_run):
        problem = mommy.make(ProblemRevision)
        subtask1 = mommy.make(Subtask, problem=problem)
        subtask2 = mommy.make(Subtask, problem=problem)
        test_case1 = create_mommy_valid_testcase(problem=problem)
        test_case2 = create_mommy_valid_testcase(problem=problem)
        test_case3 = create_mommy_valid_testcase(problem=problem)
        subtask1.testcases.add(test_case1)
        subtask1.testcases.add(test_case2)
        subtask2.testcases.add(test_case1)
        subtask2.testcases.add(test_case2)
        subtask2.testcases.add(test_case3)
        subtask1.save()
        subtask2.save()
        validator = mommy.make(Validator, global_validator=False, problem=problem)
        validator._subtasks.add(subtask1)
        validator._subtasks.add(subtask2)
        validator.save()
        validator.validate()
        self.assertEqual(validator.validatorresult_set.all().count(), 3)

    @mock.patch(target='problems.models.validator.ValidatorResult.run')
    def test_creation_of_validator_result_with_all_subtasks_of_one_problem(self, mock_run):
        problem = mommy.make(ProblemRevision)
        subtask1 = mommy.make(Subtask, problem=problem)
        subtask2 = mommy.make(Subtask, problem=problem)
        test_case1 = create_mommy_valid_testcase(problem=problem)
        test_case2 = create_mommy_valid_testcase(problem=problem)
        test_case3 = create_mommy_valid_testcase(problem=problem)
        subtask1.testcases.add(test_case1)
        subtask1.testcases.add(test_case2)
        subtask2.testcases.add(test_case3)
        validator = mommy.make(Validator, global_validator=True, problem=problem)
        validator.validate()
        self.assertEqual(validator.validatorresult_set.all().count(), 3)

    def test_successful_validation(self):
        problem = mommy.make(ProblemRevision)
        hello_world_testcase = \
            create_mommy_valid_testcase(
                input_static_file=get_resource_as_file_model("statics", "hello_world.txt"),
                problem=problem
            )
        bye_world_testcase = \
            create_mommy_valid_testcase(
                input_static_file=get_resource_as_file_model("statics", "bye_world.txt"),
                problem=problem
            )
        validator = Validator(
            name="assert_hello_world.cpp",
            problem=problem,
            global_validator=True,
            source_file=get_resource_as_file_model("codes", "assert_hello_world.cpp"),
            source_language="c++",
        )
        validator.save()
        validator.validate()
        validator.refresh_from_db()
        self.assertEqual(validator.validatorresult_set.all().count(), 2)
        self.assertEqual(validator.validatorresult_set.filter(valid=True).count(), 1)
        self.assertEqual(validator.validatorresult_set.filter(valid=False).count(), 1)
        self.assertTrue(
            "Hello World" in
            validator.validatorresult_set.get(valid=False).validation_message,
        )
