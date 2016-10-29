# Amirmohsen Ahanchi


class Runnable(object):

    def execute(self):
        raise NotImplementedError("This must be implemented in subclass")

    def run(self):
        """
        Runs runnable using task queue (e.g. Celery).
        """
        return self.execute()
