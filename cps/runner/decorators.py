from celery.contrib.methods import task_method
from django_cereal.pickle import task as cereal_task


def allow_async_function(func):
    task = cereal_task(func)
    func.async = task.delay
    return func


def allow_async_method(func):
    task = cereal_task(func, filter=task_method)
    func.async = func
    return func
