from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models.problem_data import ProblemData


class OverviewForm(ProblemObjectModelForm):
    class Meta:
        model = ProblemData
        fields = ['code', 'name', 'title', 'time_limit', 'memory_limit', 'task_type', 'description']

    def __init__(self, *args, **kwargs):
        super(OverviewForm, self).__init__(*args, **kwargs)
        self.fields["task_type"] = forms.ChoiceField(
            choices=[(x, x) for x in self.revision.get_judge().get_task_types()]
        )

    def save(self, commit=True):
        super(OverviewForm, self).save(commit=False)
        if commit:
            self.instance.save()
            self.save_m2m()
