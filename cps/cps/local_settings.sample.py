JUDGE_DEFAULT_NAME = 'local_runner'

JUDGE_HANDLERS = {
    'local_runner': {
        'class': 'judges.runner.Runner',
        'parameters': {
            'compile_time_limit': 30,
            'compile_memory_limit': 1024,
        }
    }
}