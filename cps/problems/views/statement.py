from django.core.urlresolvers import reverse

from problems.forms.statement import StatementForm
from problems.views.generics import ProblemObjectEditView, RevisionObjectView


class EditStatement(ProblemObjectEditView):
    template_name = "problems/statement.html"
    model_form = StatementForm
    permissions_required = "observe"
    http_method_names_requiring_edit_access = RevisionObjectView.http_method_names_requiring_edit_access

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:statement", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.problem_data
