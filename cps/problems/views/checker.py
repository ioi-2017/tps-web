from django.core.urlresolvers import reverse
from problems.forms.checker import ChooseCheckerForm
from problems.views.generics import ProblemObjectEditView, RevisionObjectView


class CheckerChooseView(ProblemObjectEditView):
    template_name = "problems/checker.html"
    model_form = ChooseCheckerForm
    permissions_required = ["choose_checker"]
    http_method_names_requiring_edit_access = RevisionObjectView.http_method_names_requiring_edit_access

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:checker", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.problem_data
