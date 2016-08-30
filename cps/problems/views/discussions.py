from django.views.generic import View
from django.shortcuts import render

from .decorators import authenticate_problem_access


class DiscussionsListView(View):

    @authenticate_problem_access("read_discussions")
    def get(self, request, problem):
        return render(request, "problems/discussions_list.html", context={"discussions": problem.discussions.all()})

