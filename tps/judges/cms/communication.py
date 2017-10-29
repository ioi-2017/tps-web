# coding=utf-8

from .cmstasktype import CMSTaskType
import json
from django import forms


class Communication(CMSTaskType):

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
                                 time_limit, memory_limit, 'Communication')

    def get_parameters_form(self):
        class ParamsForm(forms.Form):
            task_type_parameters_Communication_num_processes = \
                forms.IntegerField(label='Number of Processes')

            def save(self, revision):
                # Shortcut for easier use
                problem_data = revision.problem_data

                if problem_data.task_type_parameters is None or \
                        problem_data.task_type_parameters == '':
                    problem_data.task_type_parameters = '{}'
                parameters = json.loads(problem_data.task_type_parameters)

                new_parameters = {
                    'task_type_parameters_Communication_num_processes':
                        self.cleaned_data['task_type_parameters_Communication_num_processes'],
                }
                parameters.update(new_parameters)
                problem_data.task_type_parameters = json.dumps(parameters)
                problem_data.save()

            def to_payload(self):
                fields = ['task_type_parameters_Communication_num_processes']
                defaults = ['None']
                errors = self.errors.as_data()
                res = dict()
                for num in range(len(fields)):
                    field = fields[num]
                    default = defaults[num]
                    if field in errors:
                        res[field] = default
                    else:
                        res[field] = self.cleaned_data[field]
                return res

        return ParamsForm
