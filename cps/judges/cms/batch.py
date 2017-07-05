# coding=utf-8

from .cmstasktype import CMSTaskType
import json
from django import forms


class Batch(CMSTaskType):

    def initialize_problem(
            self,
            problem_code,
            task_type_parameters,
            helpers,
            time_limit,
            memory_limit,
    ):
        return self.init_problem(problem_code, task_type_parameters, helpers,
                                 time_limit, memory_limit, 'Batch')

    def get_parameters_form(self):
        class ParamsForm(forms.Form):
            task_type_parameters_Batch_compilation = forms.ChoiceField(
                label='Compilation',
                choices=[
                    ('grader', 'Submissions are compiled with a grader'),
                    ('alone', 'Submissions are self-sufficient'),
                ]
            )
            task_type_parameters_Batch_io_0_inputfile = forms.CharField(
                label='Input file',
                help_text='blank for stdin/stdout',
                required=False,
            )
            task_type_parameters_Batch_io_1_outputfile = forms.CharField(
                label='Output file',
                help_text='blank for stdin/stdout',
                required=False,
            )

            def save(self, revision):
                # Shortcut for easier use
                problem_data = revision.problem_data

                if problem_data.task_type_parameters is None or \
                        problem_data.task_type_parameters == '':
                    problem_data.task_type_parameters = '{}'
                parameters = json.loads(problem_data.task_type_parameters)

                new_parameters = {
                    'task_type_parameters_Batch_compilation':
                        self.cleaned_data['task_type_parameters_Batch_compilation'],
                    'task_type_parameters_Batch_io_0_inputfile':
                        self.cleaned_data['task_type_parameters_Batch_io_0_inputfile'],
                    'task_type_parameters_Batch_io_1_outputfile':
                        self.cleaned_data['task_type_parameters_Batch_io_1_outputfile'],
                }
                parameters.update(new_parameters)
                problem_data.task_type_parameters = json.dumps(parameters)
                problem_data.save()

            def to_payload(self):
                fields = ['task_type_parameters_Batch_compilation',
                          'task_type_parameters_Batch_io_0_inputfile',
                          'task_type_parameters_Batch_io_1_outputfile']
                defaults = ['grader', '', '']
                errors = self.errors.as_data()
                res = dict()
                for num in range(len(fields)):
                    field = fields[num]
                    default = defaults[num]
                    if field in errors:
                        res[field] = default
                    else:
                        res[field] = self.cleaned_data[field]
                res['task_type_parameters_Batch_output_eval'] = 'diff'
                return res

        return ParamsForm
