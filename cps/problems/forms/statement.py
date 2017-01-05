from problems.forms.generic import ProblemObjectModelForm
from problems.models import ProblemData


class StatementForm(ProblemObjectModelForm):
    class Meta:
        model = ProblemData
        fields = ['statement', ]


