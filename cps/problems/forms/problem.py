from django import forms

from problems.models import Problem, ProblemRevision, ProblemData, ProblemFork
from django.utils.translation import ugettext as _

from django.db import transaction


class ProblemAddForm(forms.ModelForm):
    title = forms.CharField(label="Title")
    code_name = forms.CharField(label="Code name", help_text=_("Used as a short-name"))

    class Meta:
        model = Problem
        fields = []

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop("owner")
        super(ProblemAddForm, self).__init__(*args, **kwargs)

    @transaction.atomic
    def save(self, commit=True):
        super(ProblemAddForm, self).save(commit=False)
        self.instance.creator = self.owner
        self.instance.save()
        problem_revision = ProblemRevision.objects.create(author=self.owner, problem=self.instance)
        problem_revision.commit("Created problem")
        problem_fork = ProblemFork.objects.create(problem=self.instance, head=problem_revision)
        problem_data = ProblemData.objects.create(problem=problem_revision,
                                                  title=self.cleaned_data["title"],
                                                  code_name=self.cleaned_data["code_name"])
        self.instance.master_revision = problem_revision

        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
