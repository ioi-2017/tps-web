from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from judge.results import JudgeVerdict
from problems.forms.invocation import InvocationAddForm
from problems.forms.solution import SolutionAddForm
from problems.models import Solution, SolutionRun, SolutionRunResult, SolutionSubtaskExpectedVerdict
from problems.models.enums import SolutionVerdict, SolutionRunVerdict
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView

__all__ = ["InvocationsListView", "InvocationAddView", "InvocationRunView", "InvocationDetailsView",
           "InvocationAnswerDownloadView", "InvocationInputDownloadView", "InvocationOutputDownloadView",
           "InvocationResultView",]


class InvocationsListView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug):
        invocations  = self.revision.solutionrun_set.all()
        return render(request, "problems/invocations_list.html", context={
            "invocations": invocations
        })


class InvocationAddView(ProblemObjectAddView):
    template_name = "problems/add_invocation.html"
    model_form = InvocationAddForm
    permissions_required = ["add_invocation"]
    http_method_names_requiring_edit_access = []

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:invocations", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })


class InvocationRunView(RevisionObjectView):
    http_method_names_requiring_edit_access = []

    def post(self, request, problem_code, revision_slug, invocation_id):
        invocations = SolutionRun.objects.all()
        obj = get_object_or_404(SolutionRun, **{
            "base_problem_id": self.problem.id,
            "commit_id": self.revision.commit_id,
            "id": invocation_id
        })
        obj.run()
        return HttpResponseRedirect(reverse("problems:invocations", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        }))


class InvocationDetailsView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug, invocation_id):
        obj = get_object_or_404(SolutionRun, **{
            "base_problem_id": self.problem.id,
            "commit_id": self.revision.commit_id,
            "id": invocation_id
        })
        if not obj.started():
            return HttpResponseRedirect(reverse("problems:invocations", kwargs={
                "problem_code": problem_code,
                "revision_slug": revision_slug
            }))

        invocation_results = obj.results.all()
        dic = {}
        testcases = obj.testcases.all()
        for testcase in testcases:
            dic[testcase.pk] = {}
        for invocation_result in invocation_results:
            dic[invocation_result.testcase_id][invocation_result.solution_id] = invocation_result
        solutions = obj.solutions.all()
        results = []

        for testcase in testcases:
            current_results = []
            failed_subtasks = []
            for solution in solutions:
                testcase_subtasks = []
                current_results.append(dic[testcase.pk][solution.pk])
                if not dic[testcase.pk][solution.pk].validate():
                    testcase_subtasks.append((None, solution.verdict.short_name))
                for subtask in testcase.subtasks.all():
                    if not dic[testcase.pk][solution.pk].validate(subtasks=[subtask]):
                        try:
                            subtask_verdict = solution.subtask_verdicts[subtask.name]
                            short_name = subtask_verdict.short_name
                        except KeyError:
                            short_name = solution.verdict.short_name
                        testcase_subtasks.append((subtask, short_name))
                failed_subtasks.append(testcase_subtasks)
            results.append((testcase, zip(current_results, failed_subtasks)))

        solution_max_time = []
        solution_max_memory = []
        for solution in solutions:
            max_time = 0
            max_memory = 0
            for testcase in testcases:
                if not dic[testcase.pk][solution.pk].solution_execution_time is None:
                    max_time = max(dic[testcase.pk][solution.pk].solution_execution_time, max_time)
                if not dic[testcase.pk][solution.pk].solution_memory_usage is None:
                    max_memory = max(dic[testcase.pk][solution.pk].solution_memory_usage, max_memory)
            solution_max_time.append(max_time)
            solution_max_memory.append(max_memory)

        validations = []
        for solution in solutions:
            validations.append((solution, obj.validate_solution(solution)))

        subtasks = self.revision.subtasks.all()

        subtasks_results = []
        testcases_pk = [t.pk for t in testcases]

        for subtask in subtasks:
            subtask_results = []
            for solution in solutions:
                subtask_solution_result = []
                validation = True
                for testcase in subtask.testcases.all():
                    if testcase.pk in testcases_pk:
                        subtask_solution_result.append(dic[testcase.pk][solution.pk].get_short_name_for_verdict())
                        validation &= dic[testcase.pk][solution.pk].validate(subtasks=[subtask])
                current_set = set(subtask_solution_result)
                subtask_solution_result = list(current_set)
                subtask_results.append((subtask_solution_result, validation))
            subtasks_results.append((subtask, subtask_results))
        max_time_and_memory = zip(solution_max_time, solution_max_memory)

        return render(request, "problems/invocation_view.html", context={
            "invocation": obj,
            "results": results,
            "validations": validations,
            "subtasks": subtasks_results,
            "max_time_and_memory": max_time_and_memory
        })


class InvocationResultView(RevisionObjectView):
    def get(self, request, problem_code, revesion_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__base_problem_id": self.problem.id,
            "solution_run__commit_id": self.revision.commit_id,
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

        subtasks = obj.testcase.subtasks.all()
        new_subtasks_list = []

        for subtask in subtasks:
            new_subtasks_list.append((subtask, obj.validate(subtasks=[subtask])))

        return render(request, "problems/invocation_result_view.html", context={
            "input": input,
            "output": output,
            "answer": answer,
            "result": obj,
            "subtasks": new_subtasks_list
        })


class InvocationOutputDownloadView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__base_problem_id": self.problem.id,
            "solution_run__commit_id": self.revision.commit_id,
        })
        if obj.verdict in [SolutionRunVerdict.ok, SolutionRunVerdict.checker_failed]:
            raise Http404()
        response = HttpResponse(obj.solution_output.file, content_type='application/file')
        name = "attachment; filename=solution.out"
        response['Content-Disposition'] = name
        return response


class InvocationInputDownloadView(RevisionObjectView):
    # FIXME: This view is equivalent to the testcase input download view
    # however we probably want to cache the input for the results. but in case
    # we decide not to, this should be removed
    def get(self, request, problem_code, revision_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__base_problem_id": self.problem.id,
            "solution_run__commit_id": self.revision.commit_id,
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
    def get(self, request, problem_code, revision_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__base_problem_id": self.problem.id,
            "solution_run__commit_id": self.revision.commit_id,
        })
        if not obj.testcase.output_file_generated():
            raise Http404()
        response = HttpResponse(obj.testcase.output_file.file, content_type='application/file')
        name = "attachment; filename={}.ans".format(str(obj.testcase))
        response['Content-Disposition'] = name
        return response
