from django.views.generic import View
from .decorators import authenticate_problem_access
from problems.views.utils import render_for_problem

__all__ = ["SolutionAddView", "SolutionDeleteView", "SolutionEditView", "SolutionsListView"]


class SolutionsListView(View):

    @authenticate_problem_access("read_solutions")
    def get(self, request, problem, revision):
        solutions = revision.solution_set.all()

        return render_for_problem(request, problem, revision, "problems/solutions_list.html", context={
            "solutions": solutions
        })


class SolutionAddView(View):
    pass


class SolutionEditView(View):
    pass


class SolutionDeleteView(View):
    pass
