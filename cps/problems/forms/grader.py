from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import Grader
from django.utils.translation import ugettext as _


class GraderEditForm(ProblemObjectModelForm):
    file = forms.FileField(label=_("Grader"), required=False)

    field_order = ["file", "language", "name", ]

    class Meta:
        model = Grader
        fields = ["full_path", "language", ]

    def __init__(self, *args, **kwargs):
        super(GraderEditForm, self).__init__(*args, **kwargs)
        self.fields["language"] = forms.ChoiceField(
            choices=[(a, a) for a in self.revision.get_judge().get_supported_languages()], required=True, )
        self.fields["name"].help_text = _("Optional")

    def save(self, commit=True):
        super(GraderEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.code = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class GraderAddForm(GraderEditForm):
    file = forms.FileField(label=_("Solution"), required=True)
