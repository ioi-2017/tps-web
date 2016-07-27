# Amirmohsen Ahanchi
from django.core.files.base import File

class Runnable(object):
    def execute(self):
        raise NotImplementedError("This must be implemented in subclass")

    def run(self):
        """
        Runs runnable using task queue (e.g. Celery).
        """
        return self.execute()
