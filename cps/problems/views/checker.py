from django.core.urlresolvers import reverse
from problems.forms.checker import ChooseCheckerForm
from problems.views.generics import ProblemObjectEditView


class CheckerChooseView(ProblemObjectEditView):
    template_name = "problems/checker.html"
    model_form = ChooseCheckerForm
    permissions_required = ["choose_checker"]

    def get_success_url(self, problem, revision, obj):
        return reverse("problems:checker", kwargs={
            "problem_id": problem.id,
            "revision_id": revision.id,
        })

    def get_instance(self, problem, revision, *args, **kwargs):
        return revision.problem_data
