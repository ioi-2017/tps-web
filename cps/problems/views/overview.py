from django.core.urlresolvers import reverse

from problems.forms.overview import OverviewForm
from problems.views.generics import ProblemObjectEditView


__all__ = ["Overview"]


class Overview(ProblemObjectEditView):
    template_name = "problems/overview.html"
    model_form = OverviewForm
    permissions_required = "observe"

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:overview", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })

    def get_instance(self, request, problem, revision, *args, **kwargs):
        return revision.problem_data