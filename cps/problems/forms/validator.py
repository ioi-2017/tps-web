from django import forms

from problems.forms.files import SourceFileAddForm, SourceFileEditForm
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Validator


class ValidatorAddForm(SourceFileAddForm):
    class Meta:
        model = Validator
        # TODO add global subtask for IOI
        fields = ["name", "source_language", "_subtasks", "global_validator"]



class ValidatorEditForm(SourceFileEditForm):
    class Meta:
        model = Validator
        # TODO add global subtask for IOI
        fields = ["name", "source_language", "_subtasks", "global_validator"]
