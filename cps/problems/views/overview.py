from django.core.urlresolvers import reverse

from problems.forms.overview import OverviewForm
from problems.views.generics import ProblemObjectEditView, RevisionObjectView


__all__ = ["Overview"]


class Overview(ProblemObjectEditView):
    template_name = "problems/overview.html"
    model_form = OverviewForm
    permissions_required = "observe"
    http_method_names_requiring_edit_access = RevisionObjectView.http_method_names_requiring_edit_access

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:overview", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.problem_data