from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic import View

from problems.forms.validator import ValidatorAddForm, ValidatorEditForm
from problems.models import Validator
from problems.views.generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView, \
    ProblemObjectShowSourceView, ProblemObjectEditView

__all__ = ["ValidatorsListView", "ValidatorEditView", "ValidatorAddView",
           "ValidatorDeleteView", "ValidatorShowSourceView"]

class ValidatorsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        validators = self.revision.validator_set.all()

        return render(request, "problems/validator_list.html", context={
            "validators": validators
        })


class ValidatorEditView(ProblemObjectEditView):
    template_name = "problems/edit_validator.html"
    model_form = ValidatorEditForm
    permissions_required = ["edit_validator"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:validators", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.validator_set.get(pk=kwargs.get("validator_id"))


class ValidatorAddView(ProblemObjectAddView):
    template_name = "problems/add_validator.html"
    model_form = ValidatorAddForm
    permissions_required = ["add_validator"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:validators", kwargs={
            "problem_id": problem_id,
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
    code_field_name = "source_file"
    language_field_name = "source_language"
    instance_slug = "validator_id"

    def get_next_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:validators", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })