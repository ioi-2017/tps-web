import logging

from runner.sandbox.utils import create_sandbox, get_sandbox_execution_data_as_dict, delete_sandbox, \
    execution_successful
from runner.actions import execute_command
from runner.actions.action import ActionDescription


logger = logging.getLogger(__name__)


def execute_with_input(action: ActionDescription):

    logger.info("Starting execution with input")

    sandbox = create_sandbox()

    for filename, file_model in action.files:
        sandbox.create_file_from_storage(filename, file_model)

    for filename, file_model in action.executables:
        sandbox.create_file_from_storage(filename, file_model, executable=True)

    sandbox.allow_writing_only(action.output_files)

    sandbox_datas = []

    for command in action.commands:
        if not execute_command(
            sandbox, command,
            action.time_limit,
            action.memory_limit,
            stdin_redirect=action.stdin_redirect,
            stdout_redirect=action.stdout_redirect,
            stderr_redirect=action.stderr_redirect
        ):
            # Sandbox error
            logger.debug("Sandbox error while executing %s" % str(command))
            return False, False, None, None

        sandbox_data = get_sandbox_execution_data_as_dict(sandbox)
        sandbox_datas.append(sandbox_data)
        if not execution_successful(sandbox):
            return True, False, None, sandbox_datas

    output_files = [sandbox.get_file_to_storage(file) for file in action.output_files]

    delete_sandbox(sandbox)

    return True, True, output_files, sandbox_datas