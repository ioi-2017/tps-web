from functools import update_wrapper
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import classonlymethod
from django.views.generic import View, DeleteView

from problems.views.utils import extract_revision_data

__all__ = ["ProblemObjectDeleteView"]


class RevisionObjectView(View):

    http_method_names_requiring_edit_access = ['post', 'put', 'delete', 'patch']

    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError("You tried to pass in the %s method name as a "
                                "keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError("%s() received an invalid keyword %r. as_view "
                                "only accepts arguments that are already "
                                "attributes of the class." % (cls.__name__, key))

        def view(request, problem_id, revision_slug, *args, **kwargs):
            self = cls(**initkwargs)
            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get
            self.request = request
            self.args = args
            self.kwargs = kwargs

            self.problem, self.fork, self.revision = \
                extract_revision_data(problem_id, revision_slug)

            return self.dispatch(request, problem_id, revision_slug, *args, **kwargs)
        view.view_class = cls
        view.view_initkwargs = initkwargs

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names_requiring_edit_access and \
                not self.revision.editable(self.request.user):
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(RevisionObjectView, self).dispatch(request, *args, **kwargs)

    def _allowed_methods(self):
        allowed_methods = super(RevisionObjectView, self)._allowed_methods()

        if not self.revision.editable(self.request.user):
            allowed_methods = [allowed_method for allowed_method in allowed_methods
                               if allowed_method not in self.http_method_names_requiring_edit_access]

        return allowed_methods


class ProblemObjectDeleteView(RevisionObjectView):
    object_type = None
    permissions_required = []
    redirect_to = None
    lookup_field_name = "id"
    url_slug = "object_id"
    revision_field_name = "problem"

    def delete(self, request, problem_id, revision_slug, *args, **kwargs):
        object_id = kwargs.pop(self.url_slug, args[0] if len(args) > 0 else None)
        if not self.object_type:
            raise ImproperlyConfigured("you must specify an object type for delete view")
        if not self.redirect_to:
            raise ImproperlyConfigured("you must specify a url for redirect to after delete")
        obj = get_object_or_404(self.object_type, **{
            self.revision_field_name: self.revision,
            self.lookup_field_name: object_id
        })
        obj.delete()
        return HttpResponseRedirect(reverse(self.redirect_to, kwargs={
            "problem_id": self.problem.id,
            "revision_slug": revision_slug
        }))

    # Add support for browsers which only accept GET and POST for now.
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class ProblemObjectAddView(RevisionObjectView):
    template_name = None
    model_form = None
    required_permissions = []
    http_method_names_requiring_edit_access = \
        ['get'] + \
        RevisionObjectView.http_method_names_requiring_edit_access

    def _check_values(self):
        assert self.template_name is not None
        assert self.model_form is not None

    def __init__(self, **kwargs):
        super(ProblemObjectAddView, self).__init__(**kwargs)
        self._check_values()

    def _show_form(self, request, form):
        return render(request, self.template_name, context={
            "form": form
        })

    def post(self, request, problem_id, revision_slug, *args, **kwargs):
        form = self.model_form(request.POST, request.FILES,
                               problem=self.problem,
                               revision=self.revision,
                               owner=request.user)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(self.get_success_url(request, problem_id, revision_slug, obj))
        return self._show_form(request, form)

    def get(self, request, problem_id, revision_slug, *args, **kwargs):
        form = self.model_form(problem=self.problem,
                               revision=self.revision,
                               owner=request.user)
        return self._show_form(request, form)

    def get_success_url(self, request, problem_id, revision_slug, obj):
        raise NotImplementedError("Thist must be implemented in subclasses")


class ProblemObjectEditView(RevisionObjectView):
    template_name = None
    model_form = None
    permissions_required = []
    http_method_names_requiring_edit_access = \
        ['get'] + \
        RevisionObjectView.http_method_names_requiring_edit_access

    def _check_values(self):
        assert self.template_name is not None
        assert self.model_form is not None

    def _show_form(self, request, form):
        return render(request, self.template_name, context={
            "form": form,
        })

    def post(self, request, problem_id, revision_slug, *args, **kwargs):
        form = self.model_form(request.POST, request.FILES,
                               problem=self.problem,
                               revision=self.revision,
                               owner=request.user,
                               instance=self.get_instance(request, *args, **kwargs))
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(self.get_success_url(request, problem_id, revision_slug, obj))
        return self._show_form(request, form)

    def get(self, request, problem_id, revision_slug, *args, **kwargs):
        form = self.model_form(problem=self.problem,
                               revision=self.revision,
                               owner=request.user,
                               instance=self.get_instance(request, *args, **kwargs))
        return self._show_form(request, form)

    def get_success_url(self, request, problem_id, revision_slug, obj):
        raise NotImplementedError("This must be implemented in subclasses")

    def get_instance(self, request, *args, **kwargs):
        raise NotImplementedError("This must be implemented in subclasses")
