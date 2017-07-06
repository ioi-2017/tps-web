from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render

from problems.forms.files import SourceFileAddForm, ResourceAddForm, ResourceEditForm
from problems.models import SourceFile, Resource
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView, ProblemObjectEditView

__all__ = ["ResourceAddView", "ResourceDeleteView", "ResourceEditView", "ResourceDownloadView"]


class ResourceAddView(ProblemObjectAddView):
    template_name = "problems/add_resource.html"
    model_form = ResourceAddForm
    required_permissions = ["add_files"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return request.POST.get("next", request.GET.get("next", reverse("problems:overview", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })))


class SourceFileCompileView(RevisionObjectView):
    def post(self, request, problem_code, revision_slug, object_id):
        sourcefiles = SourceFile.objects.all()
        obj = get_object_or_404(SourceFile, **{
            "problem_id": self.revision.id,
            "id": object_id
        })
        obj.compile()
        return HttpResponseRedirect(reverse("problems:files", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        }))

class ResourceDeleteView(ProblemObjectDeleteView):

    object_type = Resource
    permissions_required = "delete_files",
    redirect_to = "problems:overview"

    def delete(self, request, problem_code, revision_slug, *args, **kwargs):
        super(ResourceDeleteView, self).delete(request, problem_code, revision_slug, *args, **kwargs)
        return HttpResponseRedirect(
            request.POST.get("next",
                             request.GET.get("next",
                                             reverse("problems:overview", kwargs={
                                                 "problem_code": problem_code,
                                                 "revision_slug": revision_slug
                                             }))))

class ResourceEditView(ProblemObjectEditView):
    template_name = "problems/edit_resource.html"
    model_form = ResourceEditForm
    permissions_required = ["edit_resource"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return request.POST.get("next", request.GET.get("next", reverse("problems:overview", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })))

    def get_instance(self, request, *args, **kwargs):
        return self.revision.resource_set.get(pk=kwargs.get("resource_id"))


class ResourceDownloadView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug, object_id):
        resource = get_object_or_404(Resource, **{
            "problem_id": self.revision.id,
            "id": object_id
        })
        response = HttpResponse(resource.file.file, content_type='application/file')
        name = "attachment; filename={}".format(str(resource.name))
        response['Content-Disposition'] = name
        return response

