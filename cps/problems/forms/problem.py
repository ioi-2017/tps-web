from django import forms

from problems.models import Problem, ProblemRevision, ProblemData, ProblemFork

from django.db import transaction


class ProblemAddForm(forms.ModelForm):
    title = forms.CharField(label="Title")

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
        problem_revision.commit()
        problem_fork = ProblemFork.objects.create(problem=self.instance, head=problem_revision)
        problem_data = ProblemData.objects.create(problem=problem_revision, title=self.cleaned_data["title"])
        self.instance.master_revision = problem_revision

        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
