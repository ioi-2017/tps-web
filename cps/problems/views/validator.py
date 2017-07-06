from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from problems.forms.validator import ValidatorAddForm, ValidatorEditForm
from problems.models import Validator
from problems.views.utils import get_git_object_or_404
from problems.views.generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView, \
    ProblemObjectShowSourceView, ProblemObjectEditView, ProblemObjectDownloadView

__all__ = ["ValidatorsListView", "ValidatorEditView", "ValidatorAddView",
           "ValidatorDeleteView", "ValidatorShowSourceView", "ValidatorDownloadView", ]


class ValidatorsListView(RevisionObjectView):

    def get(self, request, problem_code, revision_slug):
        validators = self.revision.validator_set.all()
        resources = self.revision.resource_set.all()

        return render(request, "problems/validator_list.html", context={
            "validators": validators,
            "resources": resources
        })


class ValidatorEditView(ProblemObjectEditView):
    template_name = "problems/edit_validator.html"
    model_form = ValidatorEditForm
    permissions_required = ["edit_validator"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:validators", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.validator_set.get(pk=kwargs.get("validator_id"))


class ValidatorAddView(ProblemObjectAddView):
    template_name = "problems/add_validator.html"
    model_form = ValidatorAddForm
    permissions_required = ["add_validator"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:validators", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })


ValidatorDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Validator,
    permissions_required="delete_validator",
    redirect_to="problems:validators",
    url_slug="validator_id"
)


class ValidatorShowSourceView(ProblemObjectShowSourceView):
    model = Validator
    code_field_name = "file"
    language_field_name = "source_language"
    instance_slug = "validator_id"

    def get_next_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:validators", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })


class ValidatorDownloadView(ProblemObjectDownloadView):
    def get_file(self, request, *args, **kwargs):
        return get_git_object_or_404(Validator, pk=kwargs.get('validator_id'), problem=self.revision).file.file

    def get_name(self, request, *args, **kwargs):
        return get_git_object_or_404(Validator, pk=kwargs.get('validator_id'), problem=self.revision).name
