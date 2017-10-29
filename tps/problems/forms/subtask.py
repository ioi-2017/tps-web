from problems.forms.generic import ProblemObjectModelForm
from problems.models import Subtask, TestCase


class SubtaskAddForm(ProblemObjectModelForm):

    class Meta:
        model = Subtask
        fields = ["name", "score", "testcases"]

    def __init__(self, *args, **kwargs):
        super(SubtaskAddForm, self).__init__(*args, **kwargs)
        self.fields["testcases"].queryset = TestCase.objects.filter(problem=self.revision)