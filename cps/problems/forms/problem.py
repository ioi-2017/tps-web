from django import forms

from problems.models import Problem
from django.utils.translation import ugettext as _

from django.db import transaction


class ProblemAddForm(forms.Form):
    title = forms.CharField(label="Title")
    code_name = forms.CharField(label="Code name", help_text=_("Used as a short-name"))

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop("owner")
        super(ProblemAddForm, self).__init__(*args, **kwargs)

    @transaction.atomic
    def save(self, *args, **kwargs):
        problem = Problem.create_from_template_problem(
            creator=self.owner,
            title=self.cleaned_data["title"],
            code_name=self.cleaned_data["code_name"]
        )

        return problem
