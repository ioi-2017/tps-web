from django.core.urlresolvers import reverse
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import View

from problems.forms.testcases import TestCaseAddForm

from .generics import ProblemObjectAddView, RevisionObjectView
from problems.models import TestCase

__all__ = ["TestCasesListView", "TestCaseAddView", "TestCaseInputDownloadView", "TestCaseOutputDownloadView"]


class TestCasesListView(RevisionObjectView):


    def get(self, request, problem_id, revision_slug):
        return render(request,
                      "problems/testcases_list.html",
                      context={
                          "testcases": self.revision.testcase_set.all()
                      })


class TestCaseAddView(ProblemObjectAddView):
    template_name = "problems/add_testcase.html"
    model_form = TestCaseAddForm

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:testcases", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class TestCaseInputDownloadView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem_id": self.revision.id,
            "id": testcase_id
        })
        return FileResponse(testcase.input_file.file, content_type="txt")


class TestCaseOutputDownloadView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem_id": self.revision.id,
            "id": testcase_id
        })
        return FileResponse(testcase.output_file.file, content_type="txt")