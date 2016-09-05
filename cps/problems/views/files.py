from django.core.urlresolvers import reverse
from django.views.generic import View

from problems.forms.files import SourceFileAddForm, AttachmentAddForm
from .decorators import authenticate_problem_access
from .generics import ProblemObjectDeleteView, ProblemObjectAddView
from problems.models import SourceFile, Attachment
from .utils import render_for_problem

__all__ = ["FilesListView", "SourceFileDeleteView",
           "SourceFileAddView", "AttachmentAddView", "AttachmentDeleteView"]


class FilesListView(View):
    @authenticate_problem_access("read_files")
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
    permissions_required = ["add_files"]

    def get_success_url(self, problem, revision, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem.id,
            "revision_id": revision.id,
        })


class AttachmentAddView(ProblemObjectAddView):

    template_name = "problems/add_attachment.html"
    model_form = AttachmentAddForm
    permissions_required = ["add_files"]

    def get_success_url(self, problem, revision, obj):
        return reverse("problems:files", kwargs={
            "problem_id": problem.id,
            "revision_id": revision.id,
        })


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