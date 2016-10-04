from django.core.urlresolvers import reverse
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from problems.forms.testcases import TestCaseAddForm

from .decorators import problem_view
from .generics import ProblemObjectAddView
from problems.models import TestCase

__all__ = ["TestCasesListView", "TestCaseAddView", "TestCaseInputDownloadView", "TestCaseOutputDownloadView"]


class TestCasesListView(View):

    @problem_view(required_permissions=["read_testcases"])
    def get(self, request, problem, revision):
        return render(request,
                                  "problems/testcases_list.html",
                                  context={
                                      "testcases": revision.testcase_set.all()
                                  })


class TestCaseAddView(ProblemObjectAddView):
    template_name = "problems/add_testcase.html"
    model_form = TestCaseAddForm

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:testcases", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })


class TestCaseInputDownloadView(View):
    @problem_view(required_permissions=["read_testcases"])
    def get(self, request, problem, revision, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem_id": revision.id,
            "id": testcase_id
        })
        return FileResponse(testcase.input_file.file)


class TestCaseOutputDownloadView(View):
    @problem_view(required_permissions=["read_testcases"])
    def get(self, request, problem, revision, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem_id": revision.id,
            "id": testcase_id
        })
        return FileResponse(testcase.output_file.file)