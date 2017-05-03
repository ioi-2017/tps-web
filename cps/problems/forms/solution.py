from django import forms

from core.fields import EnumChoiceField
from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Solution, SolutionSubtaskExpectedVerdict
from django.utils.translation import ugettext as _

from problems.models.enums import SolutionVerdict


class SolutionEditForm(ProblemObjectModelForm):
    _VERDICTS = [(None, _("Same as global verdict"))] + [(x.name, x) for x in list(SolutionVerdict)]
    #_VERDICTS = [(x.name, x.value[0]) for x in list(SolutionVerdict)]

    file = forms.FileField(label=_("Solution"), required=False)

    field_order = ["file", "language",  "name", "verdict", ]

    class Meta:
        model = Solution
        fields = ["name", "language", "verdict"]

    def __init__(self, *args, **kwargs):
        super(SolutionEditForm, self).__init__(*args, **kwargs)
        self.fields["language"] = forms.ChoiceField(choices=[(a, a) for a in self.revision.get_judge().get_supported_languages()], required=True, )
        self.fields["name"].help_text = _("Optional")
        self.subtask_fields = []
        verdicts_defaults = {}
        if self.instance is not None:
            for verdict in self.instance.subtask_verdicts.all():
                verdicts_defaults[verdict.subtask] = verdict.verdict
        for subtask in self.revision.subtasks.all():
            self.fields[str(subtask)] = EnumChoiceField(
                choices=self._VERDICTS,
                label=str(subtask),
                initial=verdicts_defaults.get(subtask, None),
                required=False,
            )
            self.subtask_fields.append(str(subtask))


    def save(self, commit=True):
        super(SolutionEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.code = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        self.instance.save()
        self.instance.subtask_verdicts.all().delete()
        for subtask in self.revision.subtasks.all():
            if self.cleaned_data[str(subtask)]:
                solution_subtask_verdict = SolutionSubtaskExpectedVerdict(
                    solution=self.instance, subtask=subtask,
                    verdict=self.cleaned_data[str(subtask)])
                solution_subtask_verdict.save()

        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class SolutionAddForm(SolutionEditForm):
    file = forms.FileField(label=_("Solution"), required=True)