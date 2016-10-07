from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Solution


class SolutionAddForm(ProblemObjectModelForm):

    class Meta:
        model = Solution
        fields = ["should_be_present_verdicts", "should_not_be_present_verdicts"]

    def __init__(self, *args, **kwargs):
        super(SolutionAddForm, self).__init__(*args, **kwargs)
        self.fields['sourcefile'] = forms.ModelChoiceField(
            queryset=SourceFile.objects.filter(problem=self.revision)
        )

    def save(self, commit=True):
        super(SolutionAddForm, self).save(commit=False)
        self.instance.code = self.cleaned_data['sourcefile']
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance