# coding=utf-8

"""
The judge connecting to Contest Management System
To use this judge, add the following commands into local_settings.py:

JUDGE_DEFAULT_NAME = 'cms'

CMS_API_ADDRESS = '<the-api-address-with-trailing-slash>'

JUDGE_HANDLERS = {
    'cms': {
        'class': 'judges.cms.CMS',
        'parameters': {}
    }
}
"""


from judge import Judge
from judge.results import JudgeVerdict
from .batch import Batch
from .communication import Communication
from .output_only import OutputOnly
from .two_steps import TwoSteps
import requests
import json
from django.conf import settings


class CMS(Judge):
    def __init__(self):
        self.task_types = {
            "Batch": Batch,
            "Communication": Communication,
            "OutputOnly": OutputOnly,
            "TwoSteps": TwoSteps
        }

    def get_task_types(self):
        response = requests.get(settings.CMS_API_ADDRESS + 'tasktypes/')
        if response.status_code != 200:
            raise ConnectionError("Cannot connect to CMS API")
        return json.loads(response.text)

    def get_supported_languages(self):
        response = requests.get(settings.CMS_API_ADDRESS + 'languages')
        if response.status_code != 200:
            raise ConnectionError("Cannot connect to CMS API")
        return json.loads(response.text) + ['text']

    def get_task_type(self, name, fallback_to_default=True):
        if name not in self.task_types:
            if not fallback_to_default:
                return None
            task_type = self.task_types["Batch"]
        else:
            task_type = self.task_types[name]
        return task_type(self)
