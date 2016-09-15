from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View

from problems.forms.checker import ChooseCheckerForm
from problems.views.decorators import authenticate_problem_access
from problems.views.utils import render_for_problem


class CheckerChooseView(View):
    template_name = "problems/checker.html"
    model_form = ChooseCheckerForm
    permissions_required = ["choose_checker"]

    def _show_form(self, request, problem, revision, form):
        checker = revision.problem_data.checker
        return render_for_problem(request, problem, revision, self.template_name, context={
            "form": form,
            "checker": checker
        })

    @authenticate_problem_access(permissions_required)
    def post(self, request, problem, revision, *args, **kwargs):
        form = self.model_form(request.POST, request.FILES, problem=problem, revision=revision)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(self.get_success_url(problem, revision, obj))
        return self._show_form(request, problem, revision, form)

    @authenticate_problem_access(permissions_required)
    def get(self, request, problem, revision, *args, **kwargs):
        form = self.model_form(problem=problem, revision=revision)
        return self._show_form(request, problem, revision, form)

    def get_success_url(self, problem, revision, obj):
        return reverse("problems:checker", kwargs={
            "problem_id": problem.id,
            "revision_id": revision.id,
        })
