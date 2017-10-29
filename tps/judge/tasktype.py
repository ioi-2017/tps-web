class TaskType(object):

    def __init__(self, judge):
        self.judge = judge

    def initialize_problem(
            self,
            problem_code,
            code_name,
            task_type_parameters,
            helpers,
            time_limit,
            memory_limit,
    ):
        """
        Initializes a new problem in the judge or updates an exisiting one.
        problem_code (str): A string to reference this problem in the judge. This should be a unique string.
        In case a problem with the same name have already been initialized,
        ths judge will have to update (or simply delete and recreate) that problem.
        code_name (str): The name for submitted solution files.
        task_type_parameters(str): A json encoded dictionary containing task type parameters
        helpers ([(str, FileModel)]): a list of files that are required when judging submissions
        provided by the judges. Each element is a tuple of the form (name, file)
        time_limit (float): Measured in seconds
        memory_limit (int): Measured in Megabytes
        :return (bool, str|None): returns a tuple, the first element is True if the problem was
        created/updated successfully, and False otherwise. The second argument provides details
        of the process, e.g. it migt contain the errors why the problem couldn't be created.
        """
        raise NotImplementedError

    def add_testcase(self, problem_code, testcase_code, input_file):
        """
        Adds a testcase to a problem

        problem_code (str): code used to reference the problem.
        The problem should be previously initialized by calling initialize_problem
        testcase_code (str): Name of the testcase. This value should be unique
        among testcases of this problem.
        input_file (FileModel)
        :return (bool, str|None): returns a tuple, the first element is True if the
        testcase was added successfully, and False otherwise.
        The second argument provides details of the process,
        e.g. it migt contain the errors why the testcase couldn't be created.
        """
        raise NotImplementedError

    def generate_output(self, problem_code, testcase_code, language, solution_file):
        """
        Runs a solution on the given test-case and returns the output.
        problem_code (str): code used to reference the problem.
        The problem should be previously initialized by calling initialize_problem
        testcase_code (str): Name of the testcase. The testcase should be previously added
        by calling add_testcase.
        language (str): the programming language of this solution
        solution_file ((str, FileModel)): A tuple representing a single solution.
        Each element is a tuple (name, file).

        :return EvaluationResult: The output and the details of execution of solution
        """
        raise NotImplementedError

    def get_parameters_form(self):
        """

        :return:
        """
        # TODO: write the doc string
        raise NotImplementedError
