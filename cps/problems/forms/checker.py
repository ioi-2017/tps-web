from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, ProblemData


class ChooseCheckerForm(ProblemObjectModelForm):
    class Meta:
        model = ProblemData
        fields = ['checker']

    def __init__(self, *args, **kwargs):
        super(ChooseCheckerForm, self).__init__(*args, **kwargs)
        self.fields['checker'] = forms.ModelChoiceField(
            queryset=SourceFile.objects.filter(problem=self.revision)
        )

    def save(self, commit=True):
        super(ChooseCheckerForm, self).save(commit=False)
        if commit:
            self.instance.save()
            self.save_m2m()
