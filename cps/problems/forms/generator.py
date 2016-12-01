from django import forms

from problems.forms.files import SourceFileAddForm
from problems.models import InputGenerator


class GeneratorAddForm(SourceFileAddForm):
    class Meta:
        model = InputGenerator
        fields = ["name", "source_language"]
