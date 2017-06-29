from problems.forms.generic import ProblemObjectModelForm
from problems.models import Statement


class StatementForm(ProblemObjectModelForm):
    class Meta:
        model = Statement
        fields = ['content', ]

    def __init__(self, *args, **kwargs):
        super(StatementForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget.attrs["id"] = "id_statement"


