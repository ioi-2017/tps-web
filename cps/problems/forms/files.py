from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Attachment
from django.utils.translation import ugettext as _


class SourceFileAddForm(ProblemObjectModelForm):

    file = forms.FileField(label=_("Source file"))

    class Meta:
        model = SourceFile
        fields = ['name', 'source_language']

    def __init__(self, *args, **kwargs):
        super(SourceFileAddForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(SourceFileAddForm, self).save(commit=False)
        self.instance.source_file = \
            FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


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