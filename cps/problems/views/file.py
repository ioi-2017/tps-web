from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404

from file_repository.models import FileModel
from problems.forms.file import FileAddForm, FileEditForm
from problems.models import Problem
from .generics import ProblemObjectAddView, RevisionObjectView, ProblemObjectEditView, \
    ProblemObjectShowSourceView, ProblemObjectDownloadView

__all__ = ["ProblemFilesView", "ProblemFileAddView",
           "ProblemFileDeleteView", "ProblemFileEditView", "ProblemFileShowSourceView",
           "ProblemFileDownloadView", ]


class ProblemFilesView(RevisionObjectView):
    def get(self, request, problem_id, revision_slug):
        return render(request, 'problems/problem_files.html', {
            'files': Problem.objects.get(id=problem_id).files.all()
        })


class ProblemFileAddView(ProblemObjectAddView):
    http_method_names_requiring_edit_access = []

    template_name = 'problems/add_file.html'
    model_form = FileAddForm
    permissions_required = ["add_file"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class ProblemFileDeleteView(RevisionObjectView):
    http_method_names_requiring_edit_access = []

    def post(self, request, problem_id, revision_slug, file_id):
        FileModel.objects.get(id=file_id).delete()
        return redirect(reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        }))


class ProblemFileEditView(ProblemObjectEditView):
    http_method_names_requiring_edit_access = []

    template_name = "problems/edit_file.html"
    model_form = FileEditForm
    permissions_required = ["edit_file"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.problem.files.get(pk=kwargs.get("file_id"))


class ProblemFileShowSourceView(ProblemObjectShowSourceView):
    model = FileModel
    code_field_name = "file"
    language_field_name = "name"
    instance_slug = "file_id"

    def get_next_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class ProblemFileDownloadView(ProblemObjectDownloadView):
    def get_name(self, request, *args, **kwargs):
        return get_object_or_404(FileModel, pk=kwargs['file_id']).name

    def get_file(self, request, *args, **kwargs):
        return get_object_or_404(FileModel, pk=kwargs['file_id']).file
