from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import View, DeleteView

from .utils import render_for_problem
from .decorators import authenticate_problem_access

__all__ = ["ProblemObjectDeleteView"]


class ProblemObjectDeleteView(View):

    object_type = None
    permissions_required = []
    redirect_to = None
    lookup_field_name = "id"
    revision_field_name = "problem_id"

    @authenticate_problem_access(permissions_required)
    def delete(self, request, problem, revision, object_id):
        if not self.object_type:
            raise ImproperlyConfigured("you must specify an object type for delete view")
        if not self.redirect_to:
            raise ImproperlyConfigured("you must specify a url for redirect to after delete")
        obj = get_object_or_404(self.object_type, **{
            self.revision_field_name: revision.id,
            self.lookup_field_name: object_id
        })
        obj.delete()
        return HttpResponseRedirect(reverse(self.redirect_to, kwargs={
            "problem_id": problem.id,
            "revision_id": revision.id
        }))

    # Add support for browsers which only accept GET and POST for now.
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class ProblemObjectAddView(View):
    template_name = None
    model_form = None
    permissions_required = []

    def _check_values(self):
        assert self.template_name is not None
        assert self.model_form is not None

    def _show_form(self, request, problem, revision, form):
        return render_for_problem(request, problem, revision, self.template_name, context={
            "form": form
        })

    @authenticate_problem_access(permissions_required)
    def post(self, request, problem, revision, *args, **kwargs):
        self._check_values()
        form = self.model_form(request.POST, request.FILES, problem=problem, revision=revision)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(self.get_success_url(problem, revision, obj))
        return self._show_form(request, problem, revision, form)

    @authenticate_problem_access(permissions_required)
    def get(self, request, problem, revision, *args, **kwargs):
        self._check_values()
        form = self.model_form(problem=problem, revision=revision)
        return self._show_form(request, problem, revision, form)

    def get_success_url(self, problem, revision, obj):
        raise NotImplementedError("Thist must be implemented in subclasses")