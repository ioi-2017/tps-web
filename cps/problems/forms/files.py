from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Attachment
from django.utils.translation import ugettext as _


class SourceFileEditForm(ProblemObjectModelForm):

    file = forms.FileField(label=_("Source file"), required=False)

    class Meta:
        model = SourceFile
        fields = ['name', 'source_language']

    def __init__(self, *args, **kwargs):
        super(SourceFileEditForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(SourceFileEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.source_file = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance

class SourceFileAddForm(SourceFileEditForm):
    file = forms.FileField(label=_("Source file"), required=True)



class AttachmentAddForm(ProblemObjectModelForm):

    uploaded_file = forms.FileField(label=_("Attachment file"))

    class Meta:
        model = Attachment
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super(AttachmentAddForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(AttachmentAddForm, self).save(commit=False)
        self.instance.file = \
            FileModel.objects.create(file=self.cleaned_data["uploaded_file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance