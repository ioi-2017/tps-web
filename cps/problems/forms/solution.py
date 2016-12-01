from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Solution
from django.utils.translation import ugettext as _

from problems.models.enums import SolutionVerdict


class SolutionEditForm(ProblemObjectModelForm):

    file = forms.FileField(label=_("Solution"), required=False)

    field_order = ["file", "language",  "name", "verdict", ]

    class Meta:
        model = Solution
        fields = ["name", "language", "verdict"]

    def __init__(self, *args, **kwargs):
        super(SolutionEditForm, self).__init__(*args, **kwargs)
        self.fields["language"] = forms.ChoiceField(choices=[(a, a) for a in self.revision.get_judge().get_supported_languages()], required=True, )
        self.fields["name"].help_text = _("Optional")


    def save(self, commit=True):
        super(SolutionEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.code = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class SolutionAddForm(SolutionEditForm):
    file = forms.FileField(label=_("Solution"), required=True)