from django import forms

from file_repository.models import FileModel
from problems.models import SourceFile, Attachment
from django.utils.translation import ugettext as _


class SourceFileAddForm(forms.ModelForm):

    file = forms.FileField(label=_("Source file"))

    class Meta:
        model = SourceFile
        fields = ['name', 'source_language']

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        super(SourceFileAddForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(SourceFileAddForm, self).save(commit=False)
        self.instance.source_file = \
            FileModel.objects.create(name=self.cleaned_data["file"].name, file=self.cleaned_data["file"])
        self.instance.problem = self.revision
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class AttachmentAddForm(forms.ModelForm):

    uploaded_file = forms.FileField(label=_("Attachment file"))

    class Meta:
        model = Attachment
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        super(AttachmentAddForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(AttachmentAddForm, self).save(commit=False)
        self.instance.file = \
            FileModel.objects.create(name=self.cleaned_data["uploaded_file"].name,
                                     file=self.cleaned_data["uploaded_file"])
        self.instance.problem = self.revision
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance