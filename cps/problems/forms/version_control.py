from django import forms

from problems.models import ProblemRevision


class CommitForm(forms.ModelForm):
    class Meta:
        model = ProblemRevision
        fields = ["commit_message"]

    def save(self, commit=True):
        self.instance.commit(self.cleaned_data["commit_message"])