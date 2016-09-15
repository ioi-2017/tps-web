from django import forms

from problems.models import SourceFile, ProblemData


class ChooseCheckerForm(forms.ModelForm):
    class Meta:
        model = ProblemData
        fields = []

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        super(ChooseCheckerForm, self).__init__(*args, **kwargs)
        self.fields['sourcefile'] = forms.ModelChoiceField(
            queryset=SourceFile.objects.filter(problem=self.revision)
        )

    def save(self, commit=True):
        super(ChooseCheckerForm, self).save(commit=False)
        self.revision.problem_data.checker = self.cleaned_data['sourcefile']
        self.revision.problem_data.save()
