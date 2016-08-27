from django.test import TestCase
from mock import mock
from model_mommy import mommy

from problems.models import Validator, Subtask, ProblemRevision
from problems.tests.utils import create_testcase_with_uploaded_files


class ValidatorTests(TestCase):
    @mock.patch(target='problems.models.validator.ValidatorResult.run')
    def test_creation_of_validator_result_with_one_subtask(self, mock_run):
        subtask = mommy.make(Subtask)
        test_case1 = create_testcase_with_uploaded_files()
        test_case2 = create_testcase_with_uploaded_files()
        subtask.testcases.add(test_case1)
        subtask.testcases.add(test_case2)
        validator = mommy.make(Validator, _validate_all_subtasks=False)
        validator._subtasks.add(subtask)
        validator.validate_subtasks()
        self.assertEqual(validator.validatorresult_set.all().count(), 2)

    @mock.patch(target='problems.models.validator.ValidatorResult.run')
    def test_creation_of_validator_result_with_many_subtasks(self, mock_run):
        subtask1 = mommy.make(Subtask)
        subtask2 = mommy.make(Subtask)
        test_case1 = create_testcase_with_uploaded_files()
        test_case2 = create_testcase_with_uploaded_files()
        test_case3 = create_testcase_with_uploaded_files()
        subtask1.testcases.add(test_case1)
        subtask1.testcases.add(test_case2)
        subtask2.testcases.add(test_case1)
        subtask2.testcases.add(test_case2)
        subtask2.testcases.add(test_case3)
        validator = mommy.make(Validator, _validate_all_subtasks=False)
        validator._subtasks.add(subtask1)
        validator._subtasks.add(subtask2)
        validator.validate_subtasks()
        self.assertEqual(validator.validatorresult_set.all().count(), 3)

    @mock.patch(target='problems.models.validator.ValidatorResult.run')
    def test_creation_of_validator_result_with_all_subtasks_of_one_problem(self, mock_run):
        problem = mommy.make(ProblemRevision)
        subtask1 = mommy.make(Subtask, problem=problem)
        subtask2 = mommy.make(Subtask, problem=problem)
        test_case1 = create_testcase_with_uploaded_files()
        test_case2 = create_testcase_with_uploaded_files()
        test_case3 = create_testcase_with_uploaded_files()
        subtask1.testcases.add(test_case1)
        subtask1.testcases.add(test_case2)
        subtask2.testcases.add(test_case3)
        validator = mommy.make(Validator, _validate_all_subtasks=True, problem=problem)
        validator.validate_subtasks()
        self.assertEqual(validator.validatorresult_set.all().count(), 3)
