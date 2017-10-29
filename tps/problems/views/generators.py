import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _

from problems.forms.generator import GeneratorAddForm, GeneratorEditForm
from problems.models import InputGenerator
from problems.views.generics import ProblemObjectDeleteView, ProblemObjectAddView, RevisionObjectView, \
    ProblemObjectShowSourceView, ProblemObjectEditView


__all__ = ["GeneratorsListView", "GeneratorEditView", "GeneratorAddView",
           "GeneratorDeleteView", "GeneratorShowSourceView", "GeneratorEnableView",
           "GeneratorDisableView"]
logger = logging.getLogger(__name__)


class GeneratorsListView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug):
        generators = self.revision.inputgenerator_set.all()
        resources = self.revision.resource_set.all()

        return render(request, "problems/generator_list.html", context={
            "generators": generators,
            "resources": resources,
        })


class GeneratorEditView(ProblemObjectEditView):
    template_name = "problems/edit_generator.html"
    model_form = GeneratorEditForm
    permissions_required = ["edit_generator"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:generators", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.inputgenerator_set.get(pk=kwargs.get("generator_id"))


class GeneratorAddView(ProblemObjectAddView):
    template_name = "problems/add_generator.html"
    model_form = GeneratorAddForm
    permissions_required = ["add_generator"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:generators", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })


GeneratorDeleteView = ProblemObjectDeleteView.as_view(
    object_type=InputGenerator,
    permissions_required="delete_generator",
    redirect_to="problems:generators",
    url_slug="generator_id"
)


class GeneratorShowSourceView(ProblemObjectShowSourceView):
    model = InputGenerator
    code_field_name = "file"
    language_field_name = "source_language"
    instance_slug = "generator_id"

    def get_next_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:generators", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })


class GeneratorEnableView(RevisionObjectView):
    def post(self, request, *args, **kwargs):
        generator = get_object_or_404(InputGenerator, pk=kwargs['generator_id'])

        try:
            generator.enable()
        except ValidationError as e:
            messages.error(request, "\n".join(e.messages))
        except Exception as e:
            logger.error(e, exc_info=True)
            messages.error(request, _("Error occurred while generating!"))

        return HttpResponseRedirect(reverse("problems:generators", kwargs={
            "problem_code": self.problem.code,
            "revision_slug": self.revision_slug,
        }))


class GeneratorDisableView(RevisionObjectView):
    def post(self, request, *args, **kwargs):
        generator = get_object_or_404(InputGenerator, pk=kwargs['generator_id'])
        generator.disable()
        return HttpResponseRedirect(reverse("problems:generators", kwargs={
            "problem_code": self.problem.code,
            "revision_slug": self.revision_slug
        }))
