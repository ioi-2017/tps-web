from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import View

from problems.forms.files import SourceFileAddForm, AttachmentAddForm
from .decorators import problem_view
from .generics import ProblemObjectDeleteView, ProblemObjectAddView
from problems.models import SourceFile, Attachment
from .utils import render_for_problem

__all__ = ["FilesListView", "SourceFileDeleteView",
           "SourceFileAddView", "AttachmentAddView", "AttachmentDeleteView"]


class FilesListView(View):
    @problem_view(required_permissions=["read_files"])
    def get(self, request, problem, revision):
        source_files = revision.sourcefile_set.all()
        attachments = revision.attachment_set.all()
        return render_for_problem(request, problem, revision, "problems/files_list.html", context={
            'source_files': source_files,
            'attachments': attachments
        })


class SourceFileAddView(ProblemObjectAddView):
    template_name = "problems/add_sourcefile.html"
    model_form = SourceFileAddForm
    required_permissions = ["add_files"]

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })


class AttachmentAddView(ProblemObjectAddView):
    template_name = "problems/add_attachment.html"
    model_form = AttachmentAddForm
    required_permissions = ["add_files"]

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })


class SourceFileCompileView(View):
    @problem_view(required_permissions=["compile"])
    def get(self, request, problem, revision, object_id):
        sourcefiles = SourceFile.objects.all()
        for sourcefile in sourcefiles:
            print(sourcefile.id)
        print(object_id)
        obj = get_object_or_404(SourceFile, **{
            "problem_id": revision.id,
            "id": object_id
        })
        obj.compile()
        return HttpResponseRedirect(reverse("problems:files", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        }))


SourceFileDeleteView = ProblemObjectDeleteView.as_view(
    object_type=SourceFile,
    permissions_required="delete_files",
    redirect_to="problems:files"
)

AttachmentDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Attachment,
    permissions_required="delete_files",
    redirect_to="problems:files"
)
