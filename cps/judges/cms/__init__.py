# coding=utf-8

"""
The judge connecting to Contest Management System
To use this judge, add the following commands into local_settings.py:

JUDGE_DEFAULT_NAME = 'cms'

JUDGE_HANDLERS = {
    'cms': {
        'class': 'judges.cms.CMS',
        'parameters': {
            'api_address': '<the-api-address-with-trailing-slash>',
        }
    }
}
"""


from judge import Judge
from .batch import Batch
from .communication import Communication
from .output_only import OutputOnly
from .two_steps import TwoSteps
import os


class CMS(Judge):
    def __init__(self, api_address):
        self.task_types = {
            "Batch": Batch,
            "Communication": Communication,
            "OutputOnly": OutputOnly,
            "TwoSteps": TwoSteps
        }
        self.api_address = api_address

    def get_task_types(self):
        return list(self.task_types.keys())

    def get_supported_languages(self):
        return ["C++11 / g++", "C11 / gcc", "Haskell / ghc",
                "Java 1.4 / gcj", "Java / JDK", "Pascal / fpc", "PHP",
                "Python 2 / CPython", 'text']

    def get_task_type(self, name, fallback_to_default=True):
        if name not in self.task_types:
            if not fallback_to_default:
                return None
            task_type = self.task_types["Batch"]
        else:
            task_type = self.task_types[name]
        return task_type(self)

    def detect_language(self, filename):
        extensions = {'.cpp': 'C++11 / g++',
                      '.cc': 'C++11 / g++',
                      '.cxx': 'C++11 / g++',
                      '.c++': 'C++11 / g++',
                      '.C': 'C++11 / g++',
                      '.c': 'C11 / gcc',
                      '.hs': 'Haskell / ghc',
                      '.java': 'Java 1.4 / gcj',
                      '.pas': 'Pascal / fpc',
                      '.php': 'PHP',
                      '.py': 'Python 2 / CPython',
                      '.txt': 'text'}

        name, ext = os.path.splitext(filename)
        if ext not in extensions:
            return None
        return extensions[ext]
