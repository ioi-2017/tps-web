from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from problems.forms.fields import AutoFilledField
from problems.models import ProblemRevision, ProblemBranch, Problem
from django.utils.translation import ugettext as _

from problems.models.problem import NewProblemBranch


class CommitForm(forms.ModelForm):

    class Meta:
        model = ProblemRevision
        fields = ["commit_message"]

    def save(self, *args, **kwargs):
        super(CommitForm, self).save(*args, **kwargs)
        self.instance.commit(self.cleaned_data["commit_message"])
        return self.instance


class CommitFormPullChoice(CommitForm):

    pull_from_master = forms.BooleanField(label=_("pull from master after this commit"), initial=True, required=False)

    class Meta(CommitForm.Meta):
        pass


class BranchCreationForm(forms.ModelForm):
    class Meta:
        model = NewProblemBranch
        fields = ["name", ]
        error_messages = {
            NON_FIELD_ERRORS: {
                 'unique_together': "Branch already exists",
            }
        }

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.user = kwargs.pop("user")
        super(BranchCreationForm, self).__init__(*args, **kwargs)

        #self.fields["problem"] = AutoFilledField(initial=self.problem)
        #self.fields["creator"] = AutoFilledField(initial=self.user)

        self.fields["source_branch"] = forms.ModelChoiceField(
            label=_("Source branch"),
            queryset=self.problem.branches.all(),
            to_field_name="name",
            initial="master"  # TODO: We can use current branch instead
        )

    def save(self, commit=True):

        super(BranchCreationForm, self).save(commit=False)
        self.instance.head = self.cleaned_data["source_branch"].head

        if commit:
            self.instance.save()
            self.save_m2m()

        return self.instance


class ChooseBranchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        super(ChooseBranchForm, self).__init__(*args, **kwargs)

        self.fields["source_branch"] = forms.ModelChoiceField(
            label=_("Source branch"),
            queryset=self.problem.branches.all(),
            to_field_name="name",
            initial="master"
        )


class MergeRequestAddForm(forms.Form):
    title = forms.CharField(label=_("title"), max_length=100)
    description = forms.CharField(label=_("description"), widget=forms.Textarea)