from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.shortcuts import render

from problems.forms.problem import ProblemAddForm
from problems.models import Problem

__all__ = ["ProblemsListView", "ProblemAddView"]


class ProblemsListView(View):

    def get(self, request):
        problems = Problem.objects.all()

        return render(request, "problems/problems_list.html", context={
            "problems": problems,
            "branches_disabled": getattr(settings, "DISABLE_BRANCHES", False),
        })


class ProblemAddView(View):
    template_name = "problems/add_problem.html"

    def post(self, request):
        # FIXME: change the form
        # FIXME: use code instead of id in the URL
        form = ProblemAddForm(request.POST, owner=request.user)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": obj.id,
                "revision_slug": request.user.username if settings.DISABLE_BRANCHES and False
                else obj.get_master_branch().get_slug()
            }))

        return render(request, self.template_name, context={"form": form})

    def get(self, request):
        form = ProblemAddForm(owner=request.user)
        return render(request, self.template_name, context={"form": form})
