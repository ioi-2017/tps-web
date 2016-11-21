from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from judge.results import JudgeVerdict
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


class InvocationViewView(RevisionObjectView):
    def get(self, request, problem_id, revesion_slug, invocation_id):
        obj = get_object_or_404(SolutionRun, **{
            "problem_id": self.revision.id,
            "id": invocation_id
        })
        invocation_results = obj.results.all()
        dic = {}
        for testcase in obj.testcases.all():
            dic[testcase] = {}
        for invocation_result in invocation_results:
            dic[invocation_result.testcase][invocation_result.solution] = invocation_result
        solutions = obj.solutions.all()
        results = []
        for testcase in obj.testcases.all():
            current_results = []
            for solution in solutions:
                current_results.append(dic[testcase][solution])
            results.append((testcase,current_results))
        return render(request, "problems/invocation_view.html", context={
            "invocation": obj,
            "results": results,
            "solutions": solutions,
            "judge_result": JudgeVerdict
        })