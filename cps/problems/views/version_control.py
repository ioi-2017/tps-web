from django.views.generic import View
from problems.views.decorators import problem_view

__all__ = ["MergeForksView", "CommitWorkingCopy"]


class MergeForksView(View):
    @problem_view()
    def get(self, problem, revision):
        pass


class CommitWorkingCopy(View):
    @problem_view()
    def get(self, problem, revision):
        pass