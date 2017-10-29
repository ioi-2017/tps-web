from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404

from problems.forms.subtask import SubtaskAddForm
from problems.models import Subtask
from problems.views.generics import RevisionObjectView, ProblemObjectAddView, ProblemObjectDeleteView, \
    ProblemObjectEditView
from problems.views.utils import get_git_object_or_404


class SubtasksListView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug):
        subtasks = self.revision.subtasks.all()

        return render(request, "problems/subtasks_list.html", context={
            "subtasks": subtasks
        })


class SubtaskAddView(ProblemObjectAddView):
    template_name = "problems/add_subtask.html"
    model_form = SubtaskAddForm

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:subtasks", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        })


class SubtaskDetailsView(RevisionObjectView):
    def get(self, request, problem_code, revision_slug, subtask_id):
        subtask = get_git_object_or_404(Subtask, **{
            "problem": self.revision,
            "pk": subtask_id,
        })
        testcases = subtask.testcases.all()

        return render(request,
                      "problems/subtask_details.html",
                      context={
                          "subtask": subtask,
                          "testcases": testcases
                      })


SubtaskDeleteView = ProblemObjectDeleteView.as_view(
    object_type=Subtask,
    url_slug="subtask_id",
    permissions_required="delete_subtasks",
    redirect_to="problems:subtasks"
)


class SubtaskEditView(ProblemObjectEditView):
    template_name = "problems/edit_subtask.html"
    model_form = SubtaskAddForm
    permissions_required = ["edit_subtask"]

    def get_success_url(self, request, problem_code, revision_slug, obj):
        return reverse("problems:subtask_details", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug,
            "subtask_id": obj.pk,
        })

    def get_instance(self, request, *args, **kwargs):
        return self.revision.subtasks.get(pk=kwargs.get("subtask_id"))
