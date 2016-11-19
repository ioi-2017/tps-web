from django import forms

from problems.forms.files import SourceFileAddForm
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Validator


class ValidatorAddForm(SourceFileAddForm):
    class Meta:
        model = Validator
        # TODO add global subtask for IOI
        fields = ["name", "source_language"]

    def save(self, commit=True):
        super(ValidatorAddForm, self).save(commit=False)
        self.instance.global_validator = True
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
