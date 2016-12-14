import logging

import json
import os

from .base import BaseExporter

logger = logging.getLogger(__name__)

__all__ = ["JSONExporter"]


class JSONExporter(BaseExporter):

    short_name = "json_file"

    TESTS_DIR_NAME = "tests"
    SOLUTION_DIR_NAME = "solutions"
    VALIDATOR_DIR_NAME = "validators"

    def __init__(self, revision):
        super().__init__(revision)

    def _do_export(self):

        # Exporting problem global data

        problem_data = self.revision.problem_data

        problem_data_dict = {
            "code": problem_data.code_name,
            "name": problem_data.title,
            "time_limit": problem_data.time_limit,
            "memory_limit": problem_data.memory_limit,
        }
        if problem_data.task_type:
            problem_data_dict.update({
                "task_type": problem_data.task_type,
                "task_type_params": problem_data.task_type_parameters,
            })
        if problem_data.score_type:
            problem_data_dict.update({
                "score_type": problem_data.score_type,
                "score_type_params": problem_data.score_type_parameters,
            })

        self.write_to_file(
            "{problem_code}.json".format(problem_code=problem_data.code_name),
            json.dumps(problem_data_dict)
        )

        # Exporting testcases

        self.create_directory(self.TESTS_DIR_NAME)
        ignored_testcases = []

        for testcase in self.revision.testcase_set.all():
            testcase.generate()
            if not testcase.input_file_generated() or not testcase.output_file_generated():
                ignored_testcases.append(testcase)
                logger.warning("Testcase {} couldn't be generated. Skipping".format(testcase.name))
                continue

            self.extract_from_storage_to_path(
                testcase.input_file,
                os.path.join(
                    self.TESTS_DIR_NAME,
                    "{testcase_name}.in".format(testcase_name=testcase.name)
                ),
            )
            self.extract_from_storage_to_path(
                testcase.output_file,
                os.path.join(
                    "tests",
                    "{testcase_name}.in".format(testcase_name=testcase.name)
                )

            )

        # TODO: Handle subtasks here

        # Exporting solutions

        self.create_directory(self.SOLUTION_DIR_NAME)
        for solution in self.revision.solution_set.all():
            if solution.verdict:
                solution_dir = os.path.join(self.SOLUTION_DIR_NAME, solution.verdict)
            else:
                solution_dir = os.path.join(self.SOLUTION_DIR_NAME, "unknown_verdict")
            self.create_directory(solution_dir)
            self.extract_from_storage_to_path(solution.code, os.path.join(solution_dir, solution.name))

        # Exporting model solutions data
        model_solutions = {
            "default": problem_data.model_solution.name,
        } if problem_data.model_solution is not None else {}
        # TODO: Handle model solutions subtasks here

        self.write_to_file(
            "model_solutions.json",
            json.dumps(model_solutions)
        )

        # We don't export generators. Tests are already generated so there is no use for them

        # Exporting checker( We only extract main checker)
        checker = problem_data.checker
        if checker is not None:
            self.extract_from_storage_to_path(checker.source_file, "checker_{}".format(checker.name))

        # Exporting validators
        self.create_directory(self.VALIDATOR_DIR_NAME)
        for validator in self.revision.validator_set.all():
            # TODO: Handle subtasks here
            dirs = []
            if validator.global_validator:
                dirs.append("global")
            for dir in dirs:
                full_dir = os.path.join(self.VALIDATOR_DIR_NAME, dir)
                self.create_directory(full_dir)
                self.extract_from_storage_to_path(validator.source_file, os.path.join(full_dir, validator.name))
