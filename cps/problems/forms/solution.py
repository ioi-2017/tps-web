from django import forms

from file_repository.models import FileModel
from problems.forms.generic import ProblemObjectModelForm
from problems.models import SourceFile, Solution
from django.utils.translation import ugettext as _


class SolutionAddForm(ProblemObjectModelForm):

    file = forms.FileField(label=_("Solution"))

    class Meta:
        model = Solution
        fields = ["name", "language", "should_be_present_verdicts", "should_not_be_present_verdicts"]

    def __init__(self, *args, **kwargs):
        super(SolutionAddForm, self).__init__(*args, **kwargs)
        self.fields["language"] = forms.ChoiceField(choices=[(a, a) for a in self.revision.get_judge().get_supported_languages()], required=True, )

    def save(self, commit=True):
        super(SolutionAddForm, self).save(commit=False)
        self.instance.code = \
            FileModel.objects.create(file=self.cleaned_data["file"])
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance