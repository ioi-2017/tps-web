from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models import ProblemData


class OverviewForm(ProblemObjectModelForm):
    class Meta:
        model = ProblemData
        fields = ['code_name', 'title', 'time_limit', 'memory_limit']

    def __init__(self, *args, **kwargs):
        super(OverviewForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(OverviewForm, self).save(commit=False)
        if commit:
            self.instance.save()
            self.save_m2m()
