from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from problems.forms.invocation import InvocationAddForm
from problems.forms.solution import SolutionAddForm
from .decorators import problem_view
from problems.models import Solution, SolutionRun
from .generics import ProblemObjectDeleteView, ProblemObjectAddView


class InvocationsListView(View):
    @problem_view(required_permissions=["read_invocations"])
    def get(self, request, problem, revision):
        invocations = revision.solutionrun_set.all()

        return render(request, "problems/invocations_list.html", context={
            "invocations": invocations
        })


class InvocationAddView(ProblemObjectAddView):
    template_name = "problems/add_invocation.html"
    model_form = InvocationAddForm
    permissions_required = ["add_invocation"]

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:add_invocation", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })


class InvocationRunView(View):
    @problem_view(required_permissions=["run_invocation"])
    def get(self, request, problem, revision, invocation_id):
        invocations = SolutionRun.objects.all()
        obj = get_object_or_404(SolutionRun, **{
            "problem_id": revision.id,
            "id": invocation_id
        })
        obj.run()
        return HttpResponseRedirect(reverse("problems:invocations", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        }))