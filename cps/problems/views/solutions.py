from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.utils.translation import ugettext as _
from problems.forms.solution import SolutionAddForm, SolutionEditForm
from problems.models import Solution
from problems.models.enums import SolutionVerdict
from .generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView, ProblemObjectEditView, \
    ProblemObjectShowSourceView, ProblemObjectDownloadView

__all__ = ["SolutionAddView", "SolutionDeleteView",
           "SolutionEditView", "SolutionsListView", "SolutionShowSourceView",
           "SolutionDownloadView", ]


class SolutionsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        solutions = self.revision.solution_set.all()

        return render(request, "problems/solutions_list.html", context={
            "solutions": solutions
        })


class SolutionAddView(ProblemObjectAddView):
    template_name = "problems/add_solution.html"
    model_form = SolutionAddForm
    permissions_required = ["add_solution"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:solutions", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class SolutionEditView(ProblemObjectEditView):
    template_name = "problems/edit_solution.html"
    model_form = SolutionEditForm
    permissions_required = ["edit_solution"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:solutions", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.solution_set.get(pk=kwargs.get("solution_id"))


SolutionDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Solution,
    url_slug="solution_id",
    permissions_required="delete_solutions",
    redirect_to="problems:solutions"
)


class SolutionShowSourceView(ProblemObjectShowSourceView):
    model = Solution
    code_field_name = "code"
    language_field_name = "language"
    instance_slug = "solution_id"

    def get_next_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:solutions", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


class SolutionDownloadView(ProblemObjectDownloadView):
    def get_file(self, request, *args, **kwargs):
        return get_object_or_404(Solution, id=kwargs.get('solution_id')).code.file

    def get_name(self, request, *args, **kwargs):
        return get_object_or_404(Solution, id=kwargs.get('solution_id')).name
