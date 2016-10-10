from runner import get_execution_command
from runner.models import JobFile, JobModel


def run_with_input(source_file, input_file, time_limit, memory_limit):

    SOLUTION_FILENAME = "solution"
    INPUT_FILENAME = "input.txt"
    STDOUT_FILENAME = "stdout.txt"

    execution_command = get_execution_command(source_file.source_language, SOLUTION_FILENAME)
    job = JobModel.objects.create(
            command=execution_command,
            stdout_filename=STDOUT_FILENAME,
            stdin_filename=INPUT_FILENAME,
            time_limit=time_limit,
            memory_limit=memory_limit
    )
    job.add_file(file_model=input_file, filename=INPUT_FILENAME, type=JobFile.READONLY)
    job.add_file(file_model=source_file.compiled_file(), filename=SOLUTION_FILENAME, type=JobFile.EXECUTABLE)
    job_file = job.mark_file_for_extraction(filename=STDOUT_FILENAME)
    job.run()
    job_file.refresh_from_db()
    return job_file.file_model, job.execution_time, job.execution_memory, job.exit_code


def run_checker(source_file, input_file, jury_output, contestant_output):

    SOLUTION_FILENAME = "solution"
    INPUT_FILENAME = "input.txt"
    JURY_FILENAME = "jury.out"
    CONTESTANT_FILENAME = "contestant.out"
    STDOUT_FILENAME = "stdout.txt"
    STDERR_FILENAME = "stderr.txt"

    generation_command = get_execution_command(source_file.source_language, SOLUTION_FILENAME)
    generation_command.extend([INPUT_FILENAME, JURY_FILENAME, CONTESTANT_FILENAME])
    job = JobModel.objects.create(command=generation_command,
                   stdout_filename=STDOUT_FILENAME,
                   stderr_filename=STDERR_FILENAME
                   )
    job.add_file(file_model=input_file, filename=INPUT_FILENAME, type=JobFile.READONLY)
    job.add_file(file_model=jury_output, filename=JURY_FILENAME, type=JobFile.READONLY)
    job.add_file(file_model=contestant_output, filename=CONTESTANT_FILENAME, type=JobFile.READONLY)
    job.add_file(file_model=source_file.compiled_file(), filename=SOLUTION_FILENAME, type=JobFile.EXECUTABLE)
    stdout_job_file = job.mark_file_for_extraction(filename=STDOUT_FILENAME)
    stderr_job_file = job.mark_file_for_extraction(filename=STDERR_FILENAME)
    job.run()
    stdout_job_file.refresh_from_db()
    stderr_job_file.refresh_from_db()
    score = float(stdout_job_file.file_model.file.readline())
    contestant_comment = str(stderr_job_file.file_model.file.readline())
    jury_comment = str(stderr_job_file.file_model.file.readline())
    stdout_job_file.file_model.delete()
    stderr_job_file.file_model.delete()
    return score, contestant_comment, jury_comment
