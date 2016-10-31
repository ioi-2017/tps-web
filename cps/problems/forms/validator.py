from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Validator


class ValidatorAddForm(ProblemObjectModelForm):
    class Meta:
        model = Validator
        # TODO add global subtask for IOI
        fields = []

    def __init__(self, *args, **kwargs):
        super(ValidatorAddForm, self).__init__(*args, **kwargs)
        self.fields['sourcefile'] = forms.ModelChoiceField(
            queryset=SourceFile.objects.filter(problem=self.revision)
        )

    def save(self, commit=True):
        super(ValidatorAddForm, self).save(commit=False)
        self.instance.code = self.cleaned_data['sourcefile']
        self.instance.global_validator = True
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
