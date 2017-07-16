from collections import Counter

from django.contrib import messages
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
from django.utils.translation import ugettext as _

__all__ = ["InvocationsListView", "InvocationAddView", "InvocationRunView", "InvocationDetailsView",
           "InvocationAnswerDownloadView", "InvocationInputDownloadView", "InvocationOutputDownloadView",
           "InvocationResultView", "InvocationCloneView"]


class InvocationsListView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug):
        commit_invocations = self.revision.solutionrun_set.all()
        old_invocations = self.problem.solutionrun_set.exclude(commit_id=self.revision.commit_id).all()[:5]
        return render(request, "problems/invocations_list.html", context={
            "commit_invocations": commit_invocations,
            "old_invocations": old_invocations
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
            "id": invocation_id
        })
        if not obj.started():
            return HttpResponseRedirect(reverse("problems:invocations", kwargs={
                "problem_code": problem_code,
                "revision_slug": revision_slug
            }))

        invocation_results = obj.results.all()
        dic = {}
        testcases = list(obj.testcases.all())
        for testcase in testcases:
            dic[testcase.pk] = {}
        done_results = 0
        total_results = len(invocation_results)
        for invocation_result in invocation_results:
            dic[invocation_result.testcase_id][invocation_result.solution_id] = invocation_result
            if invocation_result.verdict is not None and invocation_result.verdict != SolutionRunVerdict.judging:
                done_results += 1
        done_percent = (done_results * 100) // total_results
        solutions = list(obj.solutions.all())
        results = []

        for testcase in testcases:
            current_results = []
            failed_subtasks = []
            subtasks = list(testcase.subtasks.all())
            for solution in solutions:
                testcase_subtasks = []
                current_results.append(dic[testcase.pk][solution.pk])
                if not dic[testcase.pk][solution.pk].validate():
                    testcase_subtasks.append((None, solution.verdict.short_name))
                for subtask in subtasks:
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
        testcases_pk = [t.pk for t in testcases]
        for solution in solutions:
            max_time = 0
            max_memory = 0
            for testcase_pk in testcases_pk:
                if dic[testcase_pk][solution.pk].solution_execution_time is not None:
                    max_time = max(dic[testcase_pk][solution.pk].solution_execution_time, max_time)
                if dic[testcase_pk][solution.pk].solution_memory_usage is not None:
                    max_memory = max(dic[testcase_pk][solution.pk].solution_memory_usage, max_memory)
            solution_max_time.append(max_time)
            solution_max_memory.append(max_memory)

        validations = []
        for solution in solutions:
            validations.append((solution, obj.validate_solution(solution)))

        subtasks = list(self.revision.subtasks.all())

        subtasks_results = []

        for subtask in subtasks:
            subtask_results = []
            testcases = [t.pk for t in subtask.testcases.all()]
            for solution in solutions:
                subtask_solution_result = Counter()
                validation = True
                for testcase in testcases:
                    if testcase in testcases_pk:
                        subtask_solution_result[dic[testcase][solution.pk].get_short_name_for_verdict()] += 1
                        validation &= dic[testcase][solution.pk].validate(subtasks=[subtask])
                subtask_results.append((subtask_solution_result.items(), validation))
            subtasks_results.append((subtask, subtask_results))
        max_time_and_memory = zip(solution_max_time, solution_max_memory)

        return render(request, "problems/invocation_view.html", context={
            "invocation": obj,
            "results": results,
            "validations": validations,
            "subtasks": subtasks_results,
            "max_time_and_memory": max_time_and_memory,
            "done_results": done_results,
            "total_results": total_results,
            "percent_results": done_percent
        })


class InvocationResultView(RevisionObjectView):
    def get(self, request, problem_code, revesion_slug, invocation_id, result_id):
        obj = get_object_or_404(SolutionRunResult, **{
            "id": result_id,
            "solution_run__base_problem_id": self.problem.id,
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
        })
        if obj.solution_output is None:
            raise Http404
        file_ = obj.solution_output.file
        file_.open()
        response = HttpResponse(file_, content_type='application/file')
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
        file_ = obj.testcase.input_file.file
        file_.open()
        response = HttpResponse(file_, content_type='application/file')
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
        })
        if not obj.testcase.output_file_generated():
            raise Http404()
        file_ = obj.testcase.output_file.file
        file_.open()
        response = HttpResponse(file_, content_type='application/file')
        name = "attachment; filename={}.ans".format(str(obj.testcase))
        response['Content-Disposition'] = name
        return response


class InvocationCloneView(RevisionObjectView):
    http_method_names_requiring_edit_access = []
    def post(self, request, problem_code, revision_slug, invocation_id):
        obj = get_object_or_404(SolutionRun, **{
            "base_problem_id": self.problem.id,
            "id": invocation_id
        })
        commit_solutions = {s.name: s for s in self.revision.solution_set.all()}
        commit_testcases = {t.name: t for t in self.revision.testcase_set.all()}
        new_solutions = []
        discarded_solutions = []
        for s in obj.solutions.all():
            if s.name in commit_solutions:
                new_solutions.append(commit_solutions[s.name])
            else:
                discarded_solutions.append(s.name)
        new_testcases = []
        discarded_testcases = []
        for t in obj.testcases.all():
            if t.name in commit_testcases:
                new_testcases.append(commit_testcases[t.name])
            else:
                discarded_testcases.append(t.name)
        new_solutions = [s for s in obj.solutions if s.name in commit_solutions]
        new_testcases = [t for t in obj.testcases if t.name in commit_testcases]
        new_obj = SolutionRun.objects.create(
            base_problem=obj.base_problem,
            commit_id=self.revision.commit_id,
            solutions=new_solutions,
            testcases=new_testcases,
            creator=request.user
        )
        new_obj.run()
        message = "Cloned successfully."
        if discarded_solutions:
            message += _("The following solutions are not in this commit "
                         "and have been discarded:{discarded_solutions}.").format(
                discarded_solutions=", ".join(discarded_solutions))
        if discarded_testcases:
            message += _("The following testcases are not in this commit "
                         "and have been discarded:{discarded_testcases}.").format(
                discarded_testcases=", ".join(discarded_testcases))
        if discarded_solutions or discarded_testcases:
            messages.warning(request, message)
        else:
            messages.success(request, message)
        return HttpResponseRedirect(reverse("problems:invocations", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        }))
