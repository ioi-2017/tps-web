from django.core.urlresolvers import reverse
from django.shortcuts import render

from problems.forms.files import SourceFileEditForm
from problems.forms.generator import GeneratorAddForm
from problems.models import InputGenerator
from problems.views.generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView, \
    ProblemObjectShowSourceView, ProblemObjectEditView

__all__ = ["GeneratorsListView", "GeneratorEditView", "GeneratorAddView",
           "GeneratorDeleteView", "GeneratorShowSourceView"]

class GeneratorsListView(RevisionObjectView):

    def get(self, request, problem_id, revision_slug):
        generators = self.revision.inputgenerator_set.all()
        resources = self.revision.resource_set.all()

        return render(request, "problems/generator_list.html", context={
            "generators": generators,
            "resources": resources
        })


class GeneratorEditView(ProblemObjectEditView):
    template_name = "problems/edit_generator.html"
    model_form = SourceFileEditForm
    permissions_required = ["edit_generator"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:generators", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.inputgenerator_set.get(pk=kwargs.get("generators_id"))


class GeneratorAddView(ProblemObjectAddView):
    template_name = "problems/add_generator.html"
    model_form = GeneratorAddForm
    permissions_required = ["add_generator"]

    def get_success_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:generators", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })


GeneratorDeleteView = ProblemObjectDeleteView.as_view(
    object_type=InputGenerator,
    permissions_required="delete_validator",
    redirect_to="problems:validators",
    url_slug="validator_id"
)


class GeneratorShowSourceView(ProblemObjectShowSourceView):
    model = InputGenerator
    code_field_name = "source_file"
    language_field_name = "source_language"
    instance_slug = "generator_id"

    def get_next_url(self, request, problem_id, revision_slug, obj):
        return reverse("problems:generators", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        })