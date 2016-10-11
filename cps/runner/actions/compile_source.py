import logging

from runner.sandbox.utils import create_sandbox, delete_sandbox, get_sandbox_execution_data_as_dict
from runner.actions import run_compilation_commands
from runner.actions.action import ActionDescription


logger = logging.getLogger(__name__)


def compile_source(action: ActionDescription):

    logger.info("Starting compile process")

    sandbox = create_sandbox()

    for filename, file_model in action.files:
        sandbox.create_file_from_storage(filename, file_model)

    success = run_compilation_commands(
        sandbox, action.commands,
        time_limit=action.time_limit,
        memory_limit=action.memory_limit
    )

    sandbox_data = get_sandbox_execution_data_as_dict(sandbox)

    if not success:
        logger.error("Compilation was not successful")
        return False, None, get_sandbox_execution_data_as_dict(sandbox)

    output_files = [sandbox.get_file_to_storage(file) for file in action.output_files]

    delete_sandbox(sandbox)

    return True, output_files, sandbox_data