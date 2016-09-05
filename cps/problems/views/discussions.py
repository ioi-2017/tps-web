from django.views.generic import View

from .utils import render_for_problem
from .decorators import authenticate_problem_access

__all__ = ["DiscussionsListView"]


class DiscussionsListView(View):

    @authenticate_problem_access("read_discussions")
    def get(self, request, problem, revision):
        return render_for_problem(request, problem, revision, "problems/discussions_list.html", context={
            "discussions": problem.discussions.all()}
        )

