from django import forms

from core.templatetags.privileged_get import privileged_get
from file_repository.models import FileModel
from .generic import ProblemObjectModelForm
from problems.models import TestCase, Solution, SourceFile


class TestCaseAddForm(ProblemObjectModelForm):
    input_uploaded_file = forms.FileField(label="Input uploaded file")
    output_uploaded_file = forms.FileField(label="Output uploaded file")

    class Meta:
        model = TestCase
        fields = ['name', '_input_uploaded_file', '_input_generator', '_input_generation_parameters',
                  '_output_uploaded_file', '_solution']

    def __init__(self, *args, **kwargs):
        super(TestCaseAddForm, self).__init__(*args, **kwargs)
        self.fields["_solution"].queryset = Solution.objects.filter(problem=self.revision)
        self.fields["_input_generator"].queryset = SourceFile.objects.filter(problem=self.revision)

    def clean(self):
        cleaned_data = super(TestCaseAddForm, self).clean()
        if cleaned_data.get("input_uploaded_file") is not None:
            cleaned_data["_input_uploaded_file"] = FileModel.objects.create(
                name=self.cleaned_data["input_uploaded_file"].name,
                file=self.cleaned_data["input_uploaded_file"])
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
