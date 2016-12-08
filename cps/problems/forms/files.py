from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Resource
from django.utils.translation import ugettext as _


class SourceFileEditForm(ProblemObjectModelForm):

    file = forms.FileField(label=_("Source file"), required=False,
                           help_text=_("Leave this empty to keep the current file"))

    field_order = ['file', 'source_language', 'name']

    class Meta:
        model = SourceFile
        fields = ['source_language']

    def __init__(self, *args, **kwargs):
        super(SourceFileEditForm, self).__init__(*args, **kwargs)
        self.fields["name"].help_text = _("Optional")

    def save(self, commit=True):
        super(SourceFileEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.file = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance

class SourceFileAddForm(SourceFileEditForm):
    file = forms.FileField(label=_("Source file"), required=True)


class ResourceEditForm(ProblemObjectModelForm):

    file = forms.FileField(label=_("File"), required=False,
                           help_text=_("Leave this empty to keep the current file"))

    field_order = ['file', 'name']

    class Meta:
        model = Resource
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super(ResourceEditForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(ResourceEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.file = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class ResourceAddForm(ResourceEditForm):
    file = forms.FileField(label=_("File"), required=True)