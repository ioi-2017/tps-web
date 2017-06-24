from problems.forms.generic import ProblemObjectModelForm
from problems.models.problem_data import ProblemData


class StatementForm(ProblemObjectModelForm):
    class Meta:
        model = ProblemData
        fields = ['statement', ]


