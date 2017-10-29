import logging

from runner.sandbox.sandbox import SandboxBase
from runner.sandbox.utils import create_sandbox, delete_sandbox, get_sandbox_execution_data_as_dict
from runner.actions import run_compilation_commands, retrieve_files
from runner.actions.action import ActionDescription


logger = logging.getLogger(__name__)


def compile_source(action: ActionDescription):

    logger.info("Starting compile process")

    sandbox = create_sandbox()

    for filename, file_model in action.files:
        sandbox.create_file_from_storage(filename, file_model)

    success, stdouts, stderrs = run_compilation_commands(
        sandbox, action.commands,
        time_limit=action.time_limit,
        memory_limit=action.memory_limit
    )

    if not success:
        logger.error("Compilation failed due to sandbox error")
        return False, None, None, None, None, None

    sandbox_data = get_sandbox_execution_data_as_dict(sandbox)
    compilation_stdout = "\n====\n".join(stdouts)
    compilation_stderr = "\n====\n".join(stderrs)

    # TODO: Provide more log data regarding why execution failed
    if sandbox.get_exit_status() != SandboxBase.EXIT_OK:
        if sandbox.get_exit_status() == SandboxBase.EXIT_SANDBOX_ERROR:
            logger.error("Compilation was not successful due to sandbox error. \n")
        delete_sandbox(sandbox)
        return True, False, None, compilation_stdout, compilation_stderr, sandbox_data
    else:
        output_files = retrieve_files(sandbox, action.output_files)
        delete_sandbox(sandbox)


    return True, True, output_files, compilation_stdout, compilation_stderr, sandbox_data