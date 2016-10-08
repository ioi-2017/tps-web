from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from problems.forms.invocation import InvocationAddForm
from problems.forms.solution import SolutionAddForm
from problems.models import Solution, SolutionRun
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView


class InvocationsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        invocations = self.revision.solutionrun_set.all()

        return render(request, "problems/invocations_list.html", context={
            "invocations": invocations
        })


class InvocationAddView(ProblemObjectAddView):
    template_name = "problems/add_invocation.html"
    model_form = InvocationAddForm
    permissions_required = ["add_invocation"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:invocations", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class InvocationRunView(RevisionObjectView):
    def post(self, request, problem_id, revision_slug, invocation_id):
        invocations = SolutionRun.objects.all()
        obj = get_object_or_404(SolutionRun, **{
            "problem_id": self.revision.id,
            "id": invocation_id
        })
        obj.run()
        return HttpResponseRedirect(reverse("problems:invocations", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        }))