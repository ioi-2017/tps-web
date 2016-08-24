from celery import shared_task


def run_on_worker(func):
    def wrapper(*args, **kwargs):
        wrap_func = shared_task(func)
        wrap_func.delay(*args, **kwargs)
    return wrapper
