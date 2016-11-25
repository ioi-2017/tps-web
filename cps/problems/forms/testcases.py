from django import forms

from file_repository.models import FileModel
from .generic import ProblemObjectModelForm
from problems.models import TestCase, Solution, SourceFile


class TestCaseAddForm(ProblemObjectModelForm):
    input_uploaded_file = forms.FileField(label="Input uploaded file", required=True)
    output_uploaded_file = forms.FileField(label="Output uploaded file", required=True)

    class Meta:
        model = TestCase
        #TODO add generator and solution for IOI
        fields = ['_input_uploaded_file', '_output_uploaded_file']

    def __init__(self, *args, **kwargs):
        super(TestCaseAddForm, self).__init__(*args, **kwargs)
        # self.fields["_solution"].queryset = Solution.objects.filter(problem=self.revision)
        # self.fields["_input_generator"].queryset = SourceFile.objects.filter(problem=self.revision)

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
