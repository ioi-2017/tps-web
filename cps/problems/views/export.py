from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from problems.forms.export import ExportForm
from problems.models import ExportPackage, ExportPackageCreationTask
from problems.views.generics import RevisionObjectView


class ExportView(RevisionObjectView):
    http_method_names_requiring_edit_access = []
    template_name = "problems/export.html"

    def get_form(self):
        return ExportForm(problem=self.problem, revision=self.revision, user=self.request.user)

    def redirect_home(self):
        return HttpResponseRedirect(reverse("problems:export", kwargs={
            "problem_id": self.problem.id,
            "revision_slug": self.revision_slug
        }))

    def get(self, request, *args, **kwargs):
        return self.show(request, self.get_form())

    def post(self, request, *args, **kwargs):
        if self.branch != self.problem.get_master_branch():
            return self.redirect_home()

        form = ExportForm(request.POST, problem=self.problem, revision=self.revision, user=self.request.user)
        if form.is_valid():
            form.save()
            return self.redirect_home()

        return self.show(request, form)

    def show(self, request, form):
        is_master = (self.branch != self.problem.get_master_branch())
        return render(request, self.template_name,
                      {'form': form, 'exports': self.problem.exports.order_by('-pk'), 'is_master': is_master})


class ExportDownloadView(RevisionObjectView):
    def get(self, request, *args, **kwargs):
        export_package = get_object_or_404(ExportPackage, pk=kwargs['export_id'], revision=self.revision, problem=self.problem)
        response = HttpResponse(export_package.archive.file,
                                content_type='application/file')
        response['Content-Disposition'] = 'attachment; filename=%s' % export_package.archive.name

        return response


class ExportPackageStarterView(RevisionObjectView):
    http_method_names_requiring_edit_access = []

    def redirect_home(self):
        return HttpResponseRedirect(reverse("problems:export", kwargs={
            "problem_id": self.problem.id,
            "revision_slug": self.revision_slug
        }))

    def post(self, request, *args, **kwargs):
        export_package = get_object_or_404(ExportPackage, pk=kwargs['export_id'])

        export_package_starter = ExportPackageCreationTask()
        export_package_starter.request = export_package
        export_package_starter.save()
        export_package_starter.apply_async()

        return self.redirect_home()
