from django import forms
from django.core.exceptions import ValidationError

from file_repository.models import FileModel
from .generic import ProblemObjectModelForm
from problems.models import TestCase, Solution, SourceFile, Script
from django.utils.translation import ugettext as _


class TestCaseAddForm(ProblemObjectModelForm):

    input_uploaded_file = forms.FileField(label="Input uploaded file", required=False)
    output_uploaded_file = forms.FileField(label="Output uploaded file", required=False)
    generation_command = forms.CharField(label="Generation command", required=False)

    class Meta:
        automatically_filled_fields = [
            '_input_uploaded_file',
            '_input_generator_name',
            '_input_generation_parameters',
            '_output_uploaded_file',
        ]
        model = TestCase
        fields = automatically_filled_fields + []

    def clean(self):
        cleaned_data = super(TestCaseAddForm, self).clean()

        for field_name in self.Meta.automatically_filled_fields:
            cleaned_data[field_name] = None

        if cleaned_data.get("input_uploaded_file") is not None:
            cleaned_data["_input_uploaded_file"] = FileModel.objects.create(
                name=self.cleaned_data["input_uploaded_file"].name,
                file=self.cleaned_data["input_uploaded_file"])
        elif cleaned_data["generation_command"] == "":
            raise ValidationError(_("You must either upload an input or use a generator"))
        else:
            data = Script.get_generation_parameters_from_script_line(cleaned_data["generation_command"])
            cleaned_data.update(data)
        if cleaned_data.get("output_uploaded_file") is not None:
            cleaned_data["_output_uploaded_file"] = FileModel.objects.create(
                name=self.cleaned_data["output_uploaded_file"].name,
                file=self.cleaned_data["output_uploaded_file"])
        return cleaned_data


class TestCaseEditForm(ProblemObjectModelForm):
    input_uploaded_file = forms.FileField(label="Input uploaded file", required=False)
    output_uploaded_file = forms.FileField(label="Output uploaded file", required=False)
    generation_command = forms.CharField(label="Generation command", required=False)

    class Meta:
        automatically_filled_fields = [
            '_input_uploaded_file',
            '_input_generator_name',
            '_input_generation_parameters',
            '_output_uploaded_file',
        ]
        model = TestCase
        fields = automatically_filled_fields + []

    def __init__(self, *args, **kwargs):
        super(TestCaseEditForm, self).__init__(*args, **kwargs)
        if self.instance.input_static:
            self.fields["input_uploaded_file"].help_text = _("Leave this empty to keep the current file")
        if self.instance.output_static:
            self.fields["output_uploaded_file"].help_text = _("Leave this empty to keep the current file")
            self.fields["remove_output_uploaded_file"] = \
                forms.BooleanField(initial=False, required=False)

    def clean(self):
        cleaned_data = super(TestCaseEditForm, self).clean()

        for field_name in self.Meta.automatically_filled_fields:
            cleaned_data[field_name] = None

        if cleaned_data.get("input_uploaded_file") is not None:
            cleaned_data["_input_uploaded_file"] = FileModel.objects.create(
                name=self.cleaned_data["input_uploaded_file"].name,
                file=self.cleaned_data["input_uploaded_file"])
        elif cleaned_data["generation_command"] == "":
            if not self.instance.input_static:
                raise ValidationError(_("You must either upload an input or use a generator"))
            else:
                cleaned_data.pop("_input_uploaded_file")
        else:
            data = Script.get_generation_parameters_from_script_line(cleaned_data["generation_command"])
            cleaned_data.update(data)
        if cleaned_data.get("output_uploaded_file") is not None:
            cleaned_data["_output_uploaded_file"] = FileModel.objects.create(
                name=self.cleaned_data["output_uploaded_file"].name,
                file=self.cleaned_data["output_uploaded_file"])
        elif not cleaned_data.get("remove_output_uploaded_file", None) :
            cleaned_data.pop("_output_uploaded_file")
        return cleaned_data

    def save(self, *args, **kwargs):
        ret = super(TestCaseEditForm, self).save(*args, **kwargs)
        self.instance.invalidate()
        return ret
