# this is a list of tuples
from importlib import import_module

from django.conf import settings


class Judge(object):

    @staticmethod
    def get_judge(name=None):
        """
        name (str): The name of the judge as defined in settings
        :return (Judge): An instance of handler of the judge as defined in settings
        """

        if name is None:
            name = settings.JUDGE_DEFAULT_NAME
        handler_info = settings.JUDGE_HANDLERS[name]
        path = handler_info['class']
        mod, cls = path.rsplit(".", 1)
        return getattr(import_module(mod), cls)(**handler_info.get('parameters', {}))

    def get_task_types(self):
        """
        Returns a list of names of all task types supported by this judge
        """
        raise NotImplementedError

    def get_supported_languages(self):
        """
        Returns a list of names of all task types supported by this judge
        """
        raise NotImplementedError

    def get_task_type(self, name):
        """
        Returns the TaskType with the given name
        """
        raise NotImplementedError

    def get_score_types(self):
        """
        Returns a list of all ScoreTypes supported by this judge
        """
        raise NotImplementedError

    def get_score_type(self, name):
        """
        Returns the ScoreType with the given name
        """
        raise NotImplementedError

    def initialize_problem(
            self,
            problem_id,
            task_type,
            score_type,
            helpers,
            problem_code=None
    ):
        """
        Initializes a new problem in the judge or updates an exisiting one.
        problem_id(str) : A unique identifier for this problem.
         May be used to generate the problem code.
        task_type (TaskType): the task type used for this problem
        score_type (ScoreType): the score type used for this problem
        helpers ([(str, FileModel, str)]): a list of files that must be compiled with all solutions in that language.
        Each element is a tuple of the form (name, file, language)
        problem_code (str): If given and the problem corresponding to this code exists
         it updates the existing problem rather than creating a new one.
        :return (str): a reference code for this problem. length of this code is at most 128.
        """
        raise NotImplementedError

    def add_testcase(self, problem_code, testcase_id, input_file, time_limit, memory_limit):
        """
        Adds a testcase to a problem

        problem_code (str): code used to reference the problem provided by initialize_problem
        testcase_id (str): a unique identifier for this test case. This might be used to generate the reference code.
        Different judges might require some specific value to be passed as id.
        input_file (FileModel)
        output_file (FileModel)
        time_limit (float): Measured in seconds
        memory_limit (int): Measured in Megabytes
        :return str: a reference code for this test case. length of this code is at most 128.
        """
        raise NotImplementedError

    def generate_output(self, problem_code, language, solution_files, testcase_code):
        """
        Runs a solution on the given test-case and returns the output.
        problem_code (str): code used to reference the problem provided by initialize_problem
        language (str): the programming language of this solution
        solution_files ([(str, FileModel)]): A list of files representing a single solution.
        Each element is a tuple (name, file).
        testcase_code (str): A reference code for the test case provided by add_testcases method
        :return FileModel, EvaluationResult:
        The output and the details of execution of solution
        """
        raise NotImplementedError

    def get_score(self, problem_code, max_score, scores):
        """
        Returns the score for a set of test cases(namely a subtask)
         given the total score and a list of scores and scoring hints for
         test cases inside the set
        problem_code (str): code used to reference the problem provided by initialize_problem
        max_score (float): the maximum score possible for this set
        scores ([(float, str)]): a list containing pairs of the form (score, hint). The score is
         a number between 0 and 1 (inclusive). The hint might be empty.
        :return (float): the score for the set of test cases in the range [0, max_score]
        """
        raise NotImplementedError