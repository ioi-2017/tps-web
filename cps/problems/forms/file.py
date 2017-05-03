from django import forms
from django.utils.translation import ugettext as _

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm


class FileEditForm(ProblemObjectModelForm):
    file = forms.FileField(label=_("File"), required=False)
    name = forms.CharField(label=_("Name"), required=False)

    field_order = ["file", "name", ]

    class Meta:
        model = FileModel
        fields = ['file', ]

    def __init__(self, *args, **kwargs):
        super(FileEditForm, self).__init__(*args, **kwargs)
        self.fields["name"].help_text = _("Optional")

    def save(self, commit=True):

        if not commit:
            raise Exception("You shouldn't call this method with commit = False")

        super(FileEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None \
                and "name" in self.cleaned_data and self.cleaned_data["name"] is not None:

            self.instance.name = self.cleaned_data['name']
            self.instance.file = self.cleaned_data['file']

            self.instance.save()
            self.revision.problem.files.add(self.instance)
            self.save_m2m()

        return self.instance


class FileAddForm(FileEditForm):
    file = forms.FileField(label=_("File"), required=True)
    name = forms.CharField(label=_("Name"), required=False)
