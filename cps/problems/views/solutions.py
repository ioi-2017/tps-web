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

from problems.models.solution_git import GSolution
from problems.forms.solution_git import GSolutionAddForm, GSolutionEditForm

__all__ = ["SolutionAddView", "SolutionDeleteView",
           "SolutionEditView", "SolutionsListView", "SolutionShowSourceView",
           "SolutionDownloadView",

           # Git related testings
           "GSolutionAddView",
           "GSolutionEditView", "GSolutionsListView",
           ]


class SolutionsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        solutions = self.revision.solution_set.all()

        return render(request, "problems/solutions_list.html", context={
            "solutions": solutions
        })


class GSolutionsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        solutions = GSolution.objects.all()

        return render(request, "problems/solutions_list_git.html", context={
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


class GSolutionAddView(ProblemObjectAddView):
    template_name = "problems/add_solution_git.html"
    model_form = GSolutionAddForm
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


class GSolutionEditView(ProblemObjectEditView):
    template_name = "problems/edit_solution_git.html"
    model_form = GSolutionEditForm
    permissions_required = ["edit_solution"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:solutions", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        solution_pk = request.GET['pk']
        return GSolution.objects.get(pk=solution_pk)


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
