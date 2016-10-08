from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic import View
from problems.forms.solution import SolutionAddForm
from problems.models import Solution
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView

__all__ = ["SolutionAddView", "SolutionDeleteView", "SolutionEditView", "SolutionsListView"]


class SolutionsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        solutions = self.revision.solution_set.all()

        return render(request, "problems/solutions_list.html", context={
            "solutions": solutions
        })


class SolutionAddView(ProblemObjectAddView):
    template_name = "problems/add_solution.html"
    model_form = SolutionAddForm
    permissions_required = ["add_solution"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:solutions", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class SolutionEditView(View):
    pass


SolutionDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Solution,
    permissions_required="delete_solutions",
    redirect_to="problems:solutions"
)
