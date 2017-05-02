from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

from problems.forms.grader import GraderAddForm, GraderEditForm
from problems.models import Grader
from problems.views.generics import RevisionObjectView, ProblemObjectAddView, ProblemObjectShowSourceView, \
    ProblemObjectDeleteView, ProblemObjectEditView, ProblemObjectDownloadView


class GradersListView(RevisionObjectView):
    def get(self, request, problem_id, revision_slug):
        graders = self.revision.grader_set.all()

        return render(request, "problems/grader_list.html", context={
            "graders": graders
        })


class GraderAddView(ProblemObjectAddView):
    template_name = "problems/add_grader.html"
    model_form = GraderAddForm
    permissions_required = ["add_grader"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:graders", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class GraderEditView(ProblemObjectEditView):
    template_name = "problems/edit_grader.html"
    model_form = GraderEditForm
    permissions_required = ["edit_grader"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:graders", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.grader_set.get(pk=kwargs.get("grader_id"))


GraderDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Grader,
    url_slug="grader_id",
    permissions_required="delete_graders",
    redirect_to="problems:graders"
)


class GraderShowSourceView(ProblemObjectShowSourceView):
    model = Grader
    code_field_name = "code"
    language_field_name = "language"
    instance_slug = "grader_id"

    def get_next_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:graders", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class GraderDownloadView(ProblemObjectDownloadView):
    def get_file(self, request, *args, **kwargs):
        return get_object_or_404(Grader, id=kwargs.get('grader_id')).code.file

    def get_name(self, request, *args, **kwargs):
        return get_object_or_404(Grader, id=kwargs.get('grader_id')).name
