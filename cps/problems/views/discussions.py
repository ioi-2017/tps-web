from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View

from problems.forms.discussion import DiscussionAddForm, CommentAddForm
from problems.models import Discussion
from problems.views.generics import ProblemObjectAddView
from problems.views.utils import extract_revision_data

__all__ = ["DiscussionsListView", "DiscussionAddView", "CommentListView"]


class DiscussionsListView(View):
    def get(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        return render(request, "problems/discussions_list.html", context={
            "discussions": problem.discussions.all()}
        )


class DiscussionAddView(View):
    permissions_required = ["add_discussion"]

    def post(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        form = DiscussionAddForm(request.POST, request.FILES,
                                 problem=problem,
                                 owner=request.user)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:comments", kwargs={
                "problem_id": problem.id,
                "revision_slug": revision_slug,
                "discussion_id": obj.id
            }))
        return render(request, "problems/add_discussion.html", context={
            "form": form
        })

    def get(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        form = DiscussionAddForm(problem=problem, owner=request.user)
        return render(request, "problems/add_discussion.html", context={
            "form": form
        })


class CommentListView(View):
    required_permissions = ["read_comment"]

    def post(self, request, problem_id, revision_slug, discussion_id):
        discussion = get_object_or_404(Discussion, problem_id=problem_id, id=discussion_id)
        form = CommentAddForm(request.POST, request.FILES,
                              owner=request.user,
                              discussion=discussion)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:comments", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug,
                "discussion_id": discussion_id
            }))
        return render(request, "problems/comments_list.html", context={
            "comments": discussion.comments.all(),
            "form": form,
            "discussion": discussion
        })

    def get(self, request, problem_id, revision_slug, discussion_id):
        discussion = get_object_or_404(Discussion, problem_id=problem_id, id=discussion_id)
        form = CommentAddForm(owner=request.user, discussion=discussion)
        return render(request, "problems/comments_list.html", context={
            "comments": discussion.comments.all(),
            "form": form,
            "discussion": discussion
        })
