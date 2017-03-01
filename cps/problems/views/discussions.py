from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from problems.forms.discussion import DiscussionAddForm, CommentAddForm
from problems.models import Discussion
from problems.views.generics import ProblemObjectAddView, ProblemObjectView
from problems.views.utils import extract_revision_data

__all__ = ["DiscussionsListView", "DiscussionAddView", "CommentListView"]


class DiscussionsListView(ProblemObjectView):
    def get(self, request, problem_id, revision_slug):
        return render(request, "problems/discussions_list.html", context={
            "discussions": self.problem.discussions.all()}
        )


class DiscussionAddView(ProblemObjectView):
    permissions_required = ["add_discussion"]

    def post(self, request, problem_id, revision_slug):
        form = DiscussionAddForm(request.POST, request.FILES,
                                 problem=self.problem,
                                 owner=request.user)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:comments", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": revision_slug,
                "discussion_id": obj.id
            }))
        return render(request, "problems/add_discussion.html", context={
            "form": form
        })

    def get(self, request, problem_id, revision_slug):
        form = DiscussionAddForm(problem=self.problem, owner=request.user)
        return render(request, "problems/add_discussion.html", context={
            "form": form
        })


class CommentListView(ProblemObjectView):
    required_permissions = ["read_comment"]

    def post(self, request, problem_id, revision_slug, discussion_id):
        discussion = get_object_or_404(Discussion, problem_id=problem_id, id=discussion_id)
        form = CommentAddForm(request.POST, request.FILES,
                              owner=request.user,
                              topic=discussion)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:comments", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug,
                "discussion_id": discussion_id
            }))
        return render(request, "problems/discussion_comments.html", context={
            "comments": discussion.comments.all(),
            "form": form,
            "discussion": discussion
        })

    def get(self, request, problem_id, revision_slug, discussion_id):
        discussion = get_object_or_404(Discussion, problem_id=problem_id, id=discussion_id)
        form = CommentAddForm(owner=request.user, topic=discussion)
        return render(request, "problems/discussion_comments.html", context={
            "comments": discussion.comments.all(),
            "form": form,
            "discussion": discussion
        })
