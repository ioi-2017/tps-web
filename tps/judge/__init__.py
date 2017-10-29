# this is a list of tuples
from importlib import import_module

from django.conf import settings


class Judge(object):

    @staticmethod
    def get_judge(name=None):
        """
        name (str): The name of the judge as defined in settings
        :return (Judge): An instance of handler of the judge as defined in settings
        """

        if name is None:
            name = settings.JUDGE_DEFAULT_NAME
        handler_info = settings.JUDGE_HANDLERS[name]
        path = handler_info['class']
        mod, cls = path.rsplit(".", 1)
        return getattr(import_module(mod), cls)(**handler_info.get('parameters', {}))

    def get_task_types(self):
        """
        Returns a list of names of all task types supported by this judge
        """
        raise NotImplementedError

    def get_supported_languages(self):
        """
        Returns a list of names of all languages supported by this judge
        """
        raise NotImplementedError

    def get_task_type(self, name, fallback_to_default=True):
        """
        Returns the TaskType with the given name.
        if fallback to default is True and the name is invalid, return the default task type instead
        """
        raise NotImplementedError

    def detect_language(self, filename):
        """
        Returns the language name of the file, based on its filename
        """
        raise NotImplementedError
