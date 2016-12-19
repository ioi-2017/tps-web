from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.views.generic import View

from problems.forms.testcases import TestCaseAddForm, TestCaseEditForm
from problems.models.testdata import TestCaseGeneration

from .generics import ProblemObjectAddView, RevisionObjectView, ProblemObjectDeleteView, ProblemObjectEditView
from problems.models import TestCase

__all__ = ["TestCasesListView", "TestCaseAddView",
           "TestCaseDeleteView", "TestCaseEditView",
           "TestCaseGenerateView", "TestCaseDetailsView",
           "TestCaseInputDownloadView", "TestCaseOutputDownloadView"]


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


TestCaseDeleteView = ProblemObjectDeleteView.as_view(
    object_type=TestCase,
    url_slug="testcase_id",
    permissions_required="delete_testcases",
    redirect_to="problems:testcases"
)


class TestCaseEditView(ProblemObjectEditView):
    template_name = "problems/edit_testcase.html"
    model_form = TestCaseEditForm
    permissions_required = ["edit_testcase"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:testcase_details", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug,
            "testcase_id": obj.pk,
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.testcase_set.get(pk=kwargs.get("testcase_id"))


class TestCaseDetailsView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem": self.revision,
            "pk": testcase_id,
        })
        validation_results = []
        for validator in testcase.validators:
            validation_results.append(validator.get_or_create_testcase_result(testcase))


        return render(request, "problems/testcase_details.html", context={
            "testcase": testcase,
            "validation_results": validation_results
        })


class TestCaseGenerateView(RevisionObjectView):
    http_method_names_requiring_edit_access = []

    def post(self, request, problem_id, revision_slug, testcase_id=None):
        if testcase_id is None:
            testcases = self.revision.testcase_set.all()
            count = 0
            for testcase in testcases:
                if not testcase.testcase_generation_completed() and not testcase.being_generated():
                    TestCaseGeneration.objects.create(testcase=testcase).apply_async()
                    count += 1
            messages.success(request, _("Started generation of {} testcase(s).".format(count)))
            return HttpResponseRedirect(reverse("problems:testcases", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug
            }))
        else:
            testcase = get_object_or_404(TestCase, **{
                "problem": self.revision,
                "pk": testcase_id,
            })
            if testcase.testcase_generation_completed():
                messages.error(request, _("Already generated"))
            elif testcase.being_generated():
                messages.error(request, _("Generation already started"))
            else:
                TestCaseGeneration.objects.create(testcase=testcase).apply_async()
                messages.success(request, _("Generation started"))

            return HttpResponseRedirect(reverse("problems:testcase_details", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug,
                "testcase_id": testcase.pk,
            }))




class TestCaseInputDownloadView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem_id": self.revision.id,
            "id": testcase_id
        })
        file = testcase.input_file
        if testcase.input_file_generated():
            return FileResponse(file.file, content_type="txt")
        else:
            return HttpResponse(content="A problem occurred during input generation:\n{}".format(
                                        testcase.input_generation_log),
                                content_type="txt")


class TestCaseOutputDownloadView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug, testcase_id):
        testcase = get_object_or_404(TestCase, **{
            "problem_id": self.revision.id,
            "id": testcase_id
        })
        file = testcase.output_file
        if testcase.output_file_generated():
            return FileResponse(file.file, content_type="txt")
        elif testcase.input_file_generated():
            return HttpResponse(content="A problem occurred during output generation:\n{}".format(
                testcase.output_generation_log),
                content_type="txt")
        else:
            return HttpResponse(content="A problem occurred during output generation:\n{}".format(
                "Input generation failed"),
                content_type="txt")