# coding=utf-8

from .cmstasktype import CMSTaskType
import json
from django import forms


class OutputOnly(CMSTaskType):

    def initialize_problem(
            self,
            problem_code,
            code_name,
            task_type_parameters,
            helpers,
            time_limit,
            memory_limit,
    ):
        return self.init_problem(problem_code, code_name, task_type_parameters, helpers,
                                 time_limit, memory_limit, 'Batch')

    def get_parameters_form(self):
        class ParamsForm(forms.Form):

            def save(self, revision):
                pass

            def to_payload(self):
                res = {'task_type_parameters_OutputOnly_output_eval': 'diff'}
                return res

        return ParamsForm
