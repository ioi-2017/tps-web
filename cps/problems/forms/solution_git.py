from django import forms

from core.fields import EnumChoiceField
from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import GSolution, SolutionSubtaskExpectedVerdict
from django.utils.translation import ugettext as _

from problems.models.enums import SolutionVerdict


class GSolutionEditForm(ProblemObjectModelForm):
    _VERDICTS = [(None, _("Same as global verdict"))] + [(x.name, x) for x in list(SolutionVerdict)]

    file = forms.FileField(label=_("Solution"), required=False)

    field_order = ["file", "language",  "name", "verdict", ]

    class Meta:
        model = GSolution
        fields = ["name", "language", "verdict"]

    def __init__(self, *args, **kwargs):
        super(GSolutionEditForm, self).__init__(*args, **kwargs)
        self.fields["language"] = forms.ChoiceField(
            choices=[(a, a) for a in self.revision.get_judge().get_supported_languages()],
            required=True
        )
        self.fields["name"].help_text = _("Optional")

    def save(self, commit=True):
        super(GSolutionEditForm, self).save(commit=False)

        # TODO: After GitFileField
        # if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
        #     self.instance.code = \
        #         FileModel.objects.create(file=self.cleaned_data["file"])

        self.instance.save()
        return self.instance


class GSolutionAddForm(GSolutionEditForm):
    file = forms.FileField(label=_("Solution"), required=True)
