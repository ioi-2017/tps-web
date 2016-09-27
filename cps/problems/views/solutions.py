from django.core.urlresolvers import reverse
from django.views.generic import View
from problems.forms.solution import SolutionAddForm
from .decorators import problem_view
from problems.models import Solution
from .generics import ProblemObjectDeleteView, ProblemObjectAddView
from .utils import render_for_problem

__all__ = ["SolutionAddView", "SolutionDeleteView", "SolutionEditView", "SolutionsListView"]


class SolutionsListView(View):
    @problem_view(required_permissions=["read_solutions"])
    def get(self, request, problem, revision):
        solutions = revision.solution_set.all()

        return render_for_problem(request, problem, revision, "problems/solutions_list.html", context={
            "solutions": solutions
        })


class SolutionAddView(ProblemObjectAddView):
    template_name = "problems/add_solution.html"
    model_form = SolutionAddForm
    permissions_required = ["add_solution"]

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:add_solution", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })



class SolutionEditView(View):
    pass


SolutionDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Solution,
    permissions_required="delete_solutions",
    redirect_to="problems:solutions"
)
