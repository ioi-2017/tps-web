from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Solution, SolutionSubtaskExpectedScore, SolutionSubtaskExpectedVerdict
from django.utils.translation import ugettext as _

from problems.models.enums import SolutionVerdict


class SolutionEditForm(ProblemObjectModelForm):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionVerdict)]


    file = forms.FileField(label=_("Solution"), required=False)

    field_order = ["file", "language",  "name", "verdict", ]

    subtask_fields = []

    class Meta:
        model = Solution
        fields = ["name", "language", "verdict"]

    def __init__(self, *args, **kwargs):
        super(SolutionEditForm, self).__init__(*args, **kwargs)
        self.fields["language"] = forms.ChoiceField(choices=[(a, a) for a in self.revision.get_judge().get_supported_languages()], required=True, )
        self.fields["name"].help_text = _("Optional")
        for subtask in self.revision.subtasks.all():
            self.fields[str(subtask)] = forms.ChoiceField(choices=self._VERDICTS, label=str(subtask), required=False)
            self.subtask_fields.append(str(subtask))


    def save(self, commit=True):
        super(SolutionEditForm, self).save(commit=False)
        if "file" in self.cleaned_data and self.cleaned_data["file"] is not None:
            self.instance.code = \
                FileModel.objects.create(file=self.cleaned_data["file"])
        self.instance.save()
        for subtask in self.revision.subtasks.all():
            if not self.cleaned_data[str(subtask)] is None:
                solution_subtask_verdict = SolutionSubtaskExpectedVerdict(solution=self.instance, subtask=subtask,
                                                                  verdict=self.cleaned_data[str(subtask)])
                solution_subtask_verdict.save()

        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class SolutionAddForm(SolutionEditForm):
    file = forms.FileField(label=_("Solution"), required=True)