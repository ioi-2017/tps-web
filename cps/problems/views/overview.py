from django.views.generic import View

from .decorators import authenticate_problem_access
from .utils import render_for_problem

__all__ = ["Overview"]

class Overview(View):
    @authenticate_problem_access("observe")
    def get(self, request, problem, revision):
        return render_for_problem(request, problem, revision, "problems/overview.html")