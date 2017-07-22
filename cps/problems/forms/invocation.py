from django import forms

from problems.forms.fields import AutoFilledField
from problems.forms.generic import ProblemObjectModelForm, ProblemObjectForm, DBProblemObjectModelForm
from problems.models import SourceFile, Solution, SolutionRun, TestCase


class InvocationAddForm(DBProblemObjectModelForm):

    class Meta:
        model = SolutionRun
        fields = ["base_problem", "commit_id", "solutions", "testcases", "repeat_executions"]

    def save(self, commit=True):
        super(InvocationAddForm, self).save(commit=False)
        self.instance.creator = self.owner
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance