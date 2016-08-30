from django.views.generic import View
from django.shortcuts import render
from problems.models import Problem


__all__ = ["ProblemsListView"]


class ProblemsListView(View):
    def get(self, request):
        problems = Problem.objects.all().select_related("master_revision", "master_revision__problem_data")

        return render(request, "problems/problems_list.html", context={"problems": problems})