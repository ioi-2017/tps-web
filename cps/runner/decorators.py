from celery.contrib.methods import task_method
from django_cereal.pickle import task as cereal_task


def allow_async_function(func):
    task = cereal_task(func)
    return type(task.__name__, (task.__class__, ), {
        'async': lambda self, *args, **kwargs: self.delay(*args, **kwargs)
    })()


def allow_async_method(func):

    task = cereal_task(func)
    return task_method(type(task.__name__, (task.__class__, ), {
        'async': lambda self, *args, **kwargs: self(*args, **kwargs)
    })())
