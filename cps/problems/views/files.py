from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from problems.forms.files import SourceFileAddForm, AttachmentAddForm
from problems.models import SourceFile, Attachment
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView

__all__ = ["FilesListView", "SourceFileDeleteView",
           "SourceFileAddView", "AttachmentAddView", "AttachmentDeleteView"]


class FilesListView(RevisionObjectView):
    def get(self, request, problem_id, revision_slug):
        source_files = self.revision.sourcefile_set.all()
        attachments = self.revision.attachment_set.all()
        return render(request, "problems/files_list.html", context={
            'source_files': source_files,
            'attachments': attachments
        })


class SourceFileAddView(ProblemObjectAddView):
    template_name = "problems/add_sourcefile.html"
    model_form = SourceFileAddForm
    required_permissions = ["add_files"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class AttachmentAddView(ProblemObjectAddView):
    template_name = "problems/add_attachment.html"
    model_form = AttachmentAddForm
    required_permissions = ["add_files"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class SourceFileCompileView(RevisionObjectView):
    def post(self, request, problem_id, revision_slug, object_id):
        sourcefiles = SourceFile.objects.all()
        obj = get_object_or_404(SourceFile, **{
            "problem_id": self.revision.id,
            "id": object_id
        })
        obj.compile()
        return HttpResponseRedirect(reverse("problems:files", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
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
