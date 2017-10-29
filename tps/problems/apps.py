from django.apps import AppConfig


class ProblemsConfig(AppConfig):
    name = 'problems'

    def ready(self):
        super(ProblemsConfig, self).ready()
        from . import signals
