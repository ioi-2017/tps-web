import logging

import celery
from celery import current_app
from celery.app.task import _reprtask
from celery.exceptions import Retry
from celery.local import Proxy
from celery.task.base import _CompatShared
from celery.utils import gen_task_name

from tasks.serializers import DjangoPKSerializer

logger = logging.getLogger(__name__)


class TaskType(type):
    """Meta class for tasks.
    Automatically registers the task in the task registry (except
    if the :attr:`Task.abstract`` attribute is set).
    If no :attr:`Task.name` attribute is provided, then the name is generated
    from the module and class name.
    """
    _creation_count = {}  # used by old non-abstract task classes

    def __new__(cls, name, bases, attrs):
        new = super(TaskType, cls).__new__
        task_module = attrs.get('__module__') or '__main__'

        # - Abstract class: abstract attribute should not be inherited.
        abstract = attrs.pop('abstract', None)
        if abstract or not attrs.get('autoregister', True):
            return new(cls, name, bases, attrs)

        # The 'app' attribute is now a property, with the real app located
        # in the '_app' attribute.  Previously this was a regular attribute,
        # so we should support classes defining it.
        app = attrs.pop('_app', None) or attrs.pop('app', None)

        # Attempt to inherit app from one the bases
        if not isinstance(app, Proxy) and app is None:
            for base in bases:
                if getattr(base, '_app', None):
                    app = base._app
                    break
            else:
                app = current_app._get_current_object()
        attrs['_app'] = app

        # - Automatically generate missing/empty name.
        task_name = attrs.get('name')
        if not task_name:
            attrs['name'] = task_name = gen_task_name(app, name, task_module)

        if not attrs.get('_decorated'):
            # non decorated tasks must also be shared in case
            # an app is created multiple times due to modules
            # imported under multiple names.
            # Hairy stuff,  here to be compatible with 2.x.
            # People should not use non-abstract task classes anymore,
            # use the task decorator.
            from celery._state import connect_on_app_finalize
            unique_name = '.'.join([task_module, name])
            if unique_name not in cls._creation_count:
                # the creation count is used as a safety
                # so that the same task is not added recursively
                # to the set of constructors.
                cls._creation_count[unique_name] = 1
                connect_on_app_finalize(_CompatShared(
                    unique_name,
                    lambda app: TaskType.__new__(cls, name, bases,
                                                 dict(attrs, _app=app)),
                ))

        # - Create and register class.
        # Because of the way import happens (recursively)
        # we may or may not be the first time the task tries to register
        # with the framework.  There should only be one class for each task
        # name, so we always return the registered version.
        tasks = app._tasks
        if task_name not in tasks:
            tasks.register(new(cls, name, bases, attrs))
        instance = tasks[task_name]
        instance.bind(app)
        return instance.__class__

    def __repr__(cls):
        return _reprtask(cls)


class CeleryTask(celery.Task, metaclass=TaskType):

    serializer = DjangoPKSerializer.name
    DEPENDENCY_WAIT_TIME = 3
    MAX_DEPENDENCY_WAIT_TIME = 120
    track_started = True
    abstract = True
    max_retries = None

    def validate_dependencies(self, *args, **kwargs):
        # returns True if all dependencies meet,
        # None if the result is unknown(e.g. file is being compiled right now), and
        # False if the dependencies have failed. In case of failure, it is responsible
        # for storing a message explaining the reason.
        return True

    def execute_child_tasks(self, *args, **kwargs):
        pass

    def retry_countdown(self):
        return min(self.MAX_DEPENDENCY_WAIT_TIME, self.DEPENDENCY_WAIT_TIME * self.request.retries)

    def run(self, *args, **kwargs):
        try:
            result = self.validate_dependencies(*args, **kwargs)
            if result is None:
                self.retry(countdown=self.retry_countdown())
            elif result is True:
                self.execute(*args, **kwargs)
                self.execute_child_tasks(*args, **kwargs)
            else:
                logger.error("Dependencies failed to meet. Not executing")
        except Retry as e:
            raise e
        except Exception as e:
            logger.error(e, exc_info=True)
            self.retry(countdown=self.retry_countdown())

    def execute(self, *args, **kwargs):
        raise NotImplementedError
