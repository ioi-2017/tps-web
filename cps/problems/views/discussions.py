from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View

from problems.forms.discussion import DiscussionAddForm, CommentAddForm
from problems.models import Discussion
from problems.views.generics import ProblemObjectAddView
from .utils import render_for_problem
from .decorators import problem_view

__all__ = ["DiscussionsListView"]


class DiscussionsListView(View):
    @problem_view(required_permissions=["read_discussions"])
    def get(self, request, problem, revision):
        return render_for_problem(request, problem, revision, "problems/discussions_list.html", context={
            "discussions": problem.discussions.all()}
                                  )


class DiscussionAddView(ProblemObjectAddView):
    template_name = "problems/add_discussion.html"
    model_form = DiscussionAddForm
    permissions_required = ["add_discussion"]

    def get_success_url(self, request, problem, revision, obj):
        return reverse("problems:add_discussion", kwargs={
            "problem_id": problem.id,
            "revision_slug": request.resolver_match.kwargs["revision_slug"]
        })


class CommentListView(View):
    template_name = "problems/comments_list.html"
    model_form = CommentAddForm
    required_permissions = ["read_comment"]

    def _show_form(self, request, problem, revision, discussion, form):
        return render_for_problem(request, problem, revision, self.template_name, context={
            "comments": discussion.comments.all(),
            "form": form,
            "discussion": discussion
        })

    @problem_view(required_permissions=required_permissions)
    def post(self, request, problem, revision, discussion_id):
        discussion = Discussion.objects.get(id=discussion_id)
        form = self.model_form(request.POST, request.FILES, problem=problem, revision=revision, owner=request.user,
                               discussion=discussion)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:comments", kwargs={
                "problem_id": problem.id,
                "revision_slug": request.resolver_match.kwargs["revision_slug"],
                "discussion_id": discussion_id
            }))
        return self._show_form(request, problem, revision, discussion, form)

    @problem_view(required_permissions=required_permissions)
    def get(self, request, problem, revision, discussion_id):
        discussion = Discussion.objects.get(id=discussion_id)
        form = self.model_form(problem=problem, revision=revision, owner=request.user, discussion=discussion)
        return self._show_form(request, problem, revision, discussion, form)
