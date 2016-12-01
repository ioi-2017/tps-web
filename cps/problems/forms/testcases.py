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

    def __init__(self, *args, **kwargs):
        super(TestCaseAddForm, self).__init__(*args, **kwargs)

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

    def save(self, commit=True):
        super(TestCaseAddForm, self).save(commit=False)
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
