JUDGE_DEFAULT_NAME = 'local_runner'

JUDGE_HANDLERS = {
    'local_runner': {
        'class': 'judges.runner.Runner',
        'parameters': {
            'compile_time_limit': 30,
            'compile_memory_limit': 1024,
        }
    },
}

EMAIL_USE_TLS = False
EMAIL_HOST = 'localhost'
EMAIL_ADDRESS = EMAIL_HOST_USER = 'webmaster@localhost'
EMAIL_HOST_PASSWORD = 'password'