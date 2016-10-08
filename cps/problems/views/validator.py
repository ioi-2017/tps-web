from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.views.generic import View

from problems.forms.validator import ValidatorAddForm
from problems.models import Validator
from problems.views.generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView


class ValidatorsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        validators = self.revision.validator_set.all()

        return render(request, "problems/validator_list.html", context={
            "validators": validators
        })


class ValidatorEditView(View):
    pass


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
    redirect_to="problems:validators"
)
