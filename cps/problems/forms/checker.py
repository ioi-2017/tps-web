from django import forms

from problems.forms.files import SourceFileAddForm
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, ProblemData, Checker


class CheckerAddForm(SourceFileAddForm):
    class Meta:
        model = Checker
        fields = ["name", "source_language"]