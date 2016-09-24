from django import forms
from .generic import ProblemObjectModelForm
from problems.models import TestCase


class TestCaseAddForm(ProblemObjectModelForm):

    class Meta:
        model = TestCase
        fields = ('name', '_input_uploaded_file')