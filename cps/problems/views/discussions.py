from django.views.generic import View

from .utils import render_for_problem
from .decorators import problem_view

__all__ = ["DiscussionsListView"]


class DiscussionsListView(View):

    @problem_view(required_permissions=["read_discussions"])
    def get(self, request, problem, revision):
        return render_for_problem(request, problem, revision, "problems/discussions_list.html", context={
            "discussions": problem.discussions.all()}
        )

