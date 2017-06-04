from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404

from file_repository.models import FileModel
from problems.forms.file import FileAddForm, FileEditForm
from problems.models import Problem
from .generics import ProblemObjectAddView, RevisionObjectView, ProblemObjectEditView, \
    ProblemObjectShowSourceView, ProblemObjectDownloadView, ProblemObjectView
from django.utils.translation import ugettext as _

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


class ProblemFileShowSourceView(ProblemObjectView):

    def post(self, request, problem_id, revision_slug, **kwargs):
        instance_pk = kwargs.get("file_id")
        try:
            instance = self.problem.files.get(pk=instance_pk)
        except FileModel.DoesNotExist:
            raise Http404
        if "source_code" in request.POST:
            new_file = FileModel()
            new_file.file.save(instance.name, ContentFile(request.POST["source_code"]))
            new_file.save()
            self.problem.files.add(new_file)
            self.problem.files.remove(instance)
            messages.success(request, _("Saved successfully"))
            return HttpResponseRedirect(reverse("problems:file_source", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug,
                "file_id": new_file.pk
            }))
        else:
            return HttpResponseRedirect(request.get_full_path())

    def get(self, request, problem_id, revision_slug, **kwargs):
        instance_pk = kwargs.get("file_id")
        try:
            instance = self.problem.files.get(pk=instance_pk)
        except FileModel.DoesNotExist:
            raise Http404
        file_ = instance.file
        file_.open()
        code = file_.read()
        title = str(instance)
        return render(request, "problems/view_file_source.html", context={
            "code": code,
            "title": title,
            "next_url": self.get_next_url(request, problem_id, revision_slug, instance)
        })

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
