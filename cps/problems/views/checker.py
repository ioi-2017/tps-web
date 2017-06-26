from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect

from problems.forms.checker import CheckerAddForm
from problems.forms.files import SourceFileEditForm
from problems.models import Checker
from problems.views.generics import ProblemObjectEditView, RevisionObjectView, ProblemObjectAddView, \
    ProblemObjectDeleteView, ProblemObjectShowSourceView, ProblemObjectDownloadView
from problems.views.utils import get_git_object_or_404

__all__ = ["CheckerListView", "CheckerActivateView",
           "CheckerAddView", "CheckerDeleteView", "CheckerShowSourceView",
           "CheckerEditView", "CheckerDownloadView", ]


class CheckerListView(RevisionObjectView):
    def get(self, request, problem_id, revision_slug):
        checkers = self.revision.checker_set.all()
        resources = self.revision.resource_set.all()

        return render(request, "problems/checkers_list.html", context={
            "checkers": checkers,
            "resources": resources
        })


class CheckerActivateView(RevisionObjectView):
    def post(self, request, problem_id, revision_slug, checker_id):
        checker = get_object_or_404(Checker, problem=self.revision, id=checker_id)
        problem_data = self.revision.problem_data
        problem_data.checker = checker
        problem_data.save()

        return HttpResponseRedirect(reverse("problems:checkers", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        }))


class CheckerAddView(ProblemObjectAddView):
    template_name = "problems/add_checker.html"
    model_form = CheckerAddForm
    permissions_required = ["add_checker"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:checkers", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


CheckerDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Checker,
    permissions_required="delete_checkers",
    url_slug="checker_id",
    redirect_to="problems:checkers"
)


class CheckerShowSourceView(ProblemObjectShowSourceView):
    model = Checker
    code_field_name = "file"
    language_field_name = "source_language"
    instance_slug = "checker_id"

    def get_next_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:checkers", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class CheckerEditView(ProblemObjectEditView):
    template_name = "problems/edit_checker.html"
    model_form = SourceFileEditForm
    permissions_required = ["edit_checker"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:checkers", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.checker_set.get(pk=kwargs.get("checker_id"))


class CheckerDownloadView(ProblemObjectDownloadView):
    def get_file(self, request, *args, **kwargs):
        return get_git_object_or_404(self.revision.checker_set, pk=kwargs.get('checker_id')).file.file

    def get_name(self, request, *args, **kwargs):
        return get_git_object_or_404(self.revision.checker_set, pk=kwargs.get('checker_id')).name
