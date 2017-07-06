from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from problems.forms.export import ExportForm
from problems.models import ExportPackage, ExportPackageCreationTask
from problems.views.generics import RevisionObjectView, ProblemObjectDownloadView


class ExportView(RevisionObjectView):
    http_method_names_requiring_edit_access = []
    template_name = "problems/export.html"

    def get_form(self):
        return ExportForm(problem=self.problem, revision=self.revision, user=self.request.user)

    def redirect_home(self):
        return HttpResponseRedirect(reverse("problems:export", kwargs={
            "problem_code": self.problem.code,
            "revision_slug": self.revision_slug
        }))

    def get(self, request, *args, **kwargs):
        return self.show(request, self.get_form())

    def post(self, request, *args, **kwargs):
        if self.branch is not None:
            exported_revision = self.branch.head
        else:
            exported_revision = self.revision
        form = ExportForm(request.POST,
                          problem=self.problem,
                          revision=exported_revision,
                          user=self.request.user
                          )
        if form.is_valid():
            form.save()
            return self.redirect_home()

        return self.show(request, form)

    def show(self, request, form):
        return render(request, self.template_name,
                      {'form': form,
                       'exports':
                           self.problem.exports.filter(
                               creator=request.user
                           ),
                       })


class ExportDownloadView(ProblemObjectDownloadView):
    def get_name(self, request, *args, **kwargs):
        return get_object_or_404(
            ExportPackage,
            pk=kwargs['export_id'],
            problem=self.problem,
            creator=request.user,
        ).archive.name

    def get_file(self, request, *args, **kwargs):
        file_ = get_object_or_404(
            ExportPackage,
            pk=kwargs['export_id'],
            problem=self.problem,
            creator=request.user,
        ).archive
        if file_ is None:
            raise Http404
        return file_.file


class ExportPackageStarterView(RevisionObjectView):
    http_method_names_requiring_edit_access = []

    def redirect_home(self):
        return HttpResponseRedirect(reverse("problems:export", kwargs={
            "problem_code": self.problem.code,
            "revision_slug": self.revision_slug
        }))

    def post(self, request, *args, **kwargs):
        export_package = get_object_or_404(
            ExportPackage,
            pk=kwargs['export_id'],
            problem=self.problem,
            creator=request.user,
        )
        export_package.create_archive()

        return self.redirect_home()
