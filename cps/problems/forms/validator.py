from django import forms

from problems.forms.files import SourceFileAddForm, SourceFileEditForm
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Validator


class ValidatorAddForm(SourceFileAddForm):
    class Meta:
        model = Validator
        # TODO add global subtask for IOI
        fields = ["name", "source_language", "_subtasks", "global_validator"]

    def __init__(self, *args, **kwargs):
        super(ValidatorAddForm, self).__init__(*args, **kwargs)
        self.fields["_subtasks"].queryset = Validator.objects.filter(problem=self.revision)



class ValidatorEditForm(SourceFileEditForm):
    class Meta:
        model = Validator
        # TODO add global subtask for IOI
        fields = ["name", "source_language", "_subtasks", "global_validator"]

    def __init__(self, *args, **kwargs):
        super(ValidatorEditForm, self).__init__(*args, **kwargs)
        self.fields["_subtasks"].queryset = Validator.objects.filter(problem=self.revision)