from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from judge.results import JudgeVerdict
from problems.forms.invocation import InvocationAddForm
from problems.forms.solution import SolutionAddForm
from problems.models import Solution, SolutionRun, SolutionRunResult
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView

__all__ = ["InvocationsListView", "InvocationAddView", "InvocationRunView", "InvocationDetailsView"]


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


class InvocationDetailsView(RevisionObjectView):
    def get(self, request, problem_id, revision_slug, invocation_id):
        obj = get_object_or_404(SolutionRun, **{
            "problem_id": self.revision.id,
            "id": invocation_id
        })
        if not obj.started():
            return HttpResponseRedirect(reverse("problems:invocations", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug
            }))

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
            results.append((testcase, current_results))

        validations = []
        for solution in solutions:
            validations.append((solution, obj.validate_solution(solution)))

        return render(request, "problems/invocation_view.html", context={
            "invocation": obj,
            "results": results,
            "validations": validations
        })


class InvocationResultView(RevisionObjectView):
    def get(self, request, problem_id, revesion_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__problem": self.revision,
        })

        if obj.testcase.output_file_generated():
            answer = obj.testcase.output_file.get_truncated_content()
        else:
            answer = ""
        if obj.testcase.input_file_generated():
            input = obj.testcase.input_file.get_truncated_content()
        else:
            input = ""
        if obj.solution_output is None:
            output = ""
        else:
            output = obj.solution_output.get_truncated_content()
        return render(request, "problems/invocation_result_view.html", context={
            "input": input,
            "output": output,
            "answer": answer,
            "result": obj
        })


class InvocationOutputDownloadView(RevisionObjectView):
    def get(self, request, problem_id, revision_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__problem": self.revision,
        })
        if not obj.checker_execution_success:
            raise Http404()
        response = HttpResponse(obj.solution_output.file, content_type='application/file')
        name = "attachment; filename=solution.out"
        response['Content-Disposition'] = name
        return response


class InvocationInputDownloadView(RevisionObjectView):
    # FIXME: This view is equivalent to the testcase input download view
    # however we probably want to cache the input for the results. but in case
    # we decide not to, this should be removed
    def get(self, request, problem_id, revision_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__problem": self.revision,
        })
        if not obj.testcase.input_file_generated():
            raise Http404()
        response = HttpResponse(obj.testcase.input_file.file, content_type='application/file')
        name = "attachment; filename={}.in".format(str(obj.testcase))
        response['Content-Disposition'] = name
        return response


class InvocationAnswerDownloadView(RevisionObjectView):
    # FIXME: This view is equivalent to the testcase output download view
    # however we probably want to cache the input for the results. but in case
    # we decide not to, this should be removed
    def get(self, request, problem_id, revision_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__problem": self.revision,
        })
        if not obj.testcase.output_file_generated():
            raise Http404()
        response = HttpResponse(obj.testcase.output_file.file, content_type='application/file')
        name = "attachment; filename={}.ans".format(str(obj.testcase))
        response['Content-Disposition'] = name
        return response
