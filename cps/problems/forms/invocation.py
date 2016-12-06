from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Solution, SolutionRun, TestCase


class InvocationAddForm(ProblemObjectModelForm):

    class Meta:
        model = SolutionRun
        fields = ["solutions", "testcases"]

    def __init__(self, *args, **kwargs):
        super(InvocationAddForm, self).__init__(*args, **kwargs)
        self.fields["solutions"].queryset = Solution.objects.filter(problem=self.revision)
        self.fields["testcases"].queryset = TestCase.objects.filter(problem=self.revision)

    def save(self, commit=True):
        super(InvocationAddForm, self).save(commit=False)
        self.instance.creator = self.owner
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance