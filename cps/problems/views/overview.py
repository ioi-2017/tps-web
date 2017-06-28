from django.core.urlresolvers import reverse

from problems.forms.overview import OverviewForm
from problems.views.generics import RevisionObjectView
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from judge import Judge
import json


__all__ = ["Overview"]


class Overview(RevisionObjectView):
    template_name = "problems/overview.html"
    permissions_required = "observe"
    http_method_names_requiring_edit_access = RevisionObjectView.http_method_names_requiring_edit_access

    def _check_values(self):
        assert self.template_name is not None
        assert self.model_form is not None

    def _show_form(self, request, form, params_forms, instance):
        return render(request, self.template_name, context={
            "form": form,
            "params_forms": params_forms,
            "instance": instance,
        })

    def _get_params_form_class(self, task_type_name):
        task_type = Judge.get_judge().get_task_type(task_type_name)
        return task_type.get_parameters_form()

    def post(self, request, problem_id, revision_slug, *args, **kwargs):
        instance = self.get_instance(request, *args, **kwargs)
        form = OverviewForm(request.POST, request.FILES,
                            problem=self.problem,
                            revision=self.revision,
                            owner=request.user,
                            instance=instance)

        if form.is_valid():
            new_task_type = form.cleaned_data['task_type']
            if new_task_type in self.revision.get_judge().get_task_types():
                params_form = self._get_params_form_class(new_task_type)(request.POST)

                if params_form.is_valid():
                    obj = form.save()
                    params_form.save(self.revision)
                    return HttpResponseRedirect(self.get_success_url(request, problem_id, revision_slug, obj))
        return self._show_form(request, form, {new_task_type: params_form}, instance)

    def get(self, request, problem_id, revision_slug, *args, **kwargs):
        instance = self.get_instance(request, *args, **kwargs)
        form = OverviewForm(problem=self.problem,
                            revision=self.revision,
                            owner=request.user,
                            instance=instance)

        parameters_str = self.revision.problem_data.task_type_parameters
        if parameters_str is None or parameters_str == '':
            parameters_str = '{}'
        parameters = json.loads(parameters_str)

        params_forms = dict()
        for x in self.revision.get_judge().get_task_types():
            params_forms[x] = self._get_params_form_class(x)(initial=parameters)

        return self._show_form(request, form, params_forms, instance)

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:overview", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.problem_data
