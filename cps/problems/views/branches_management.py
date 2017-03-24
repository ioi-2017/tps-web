from django.contrib import messages
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from problems.forms.discussion import CommentAddForm
from problems.forms.version_control import BranchCreationForm, ChooseBranchForm, CommitForm, MergeRequestAddForm
from problems.models import SolutionRun, ProblemData, Conflict, Comment, MergeRequest
from problems.views.generics import ProblemObjectView
from problems.views.utils import get_revision_difference, diff_dict

__all__ = ["CreateBranchView", "BranchControlView", "ConflictsListView", "PullBranchView",
           "ResolveConflictView", "CreateWorkingCopy", "CommitWorkingCopy",
           "CreateMergeRequest", "MergeRequestList", "MergeRequestDiscussionView",
           "MergeRequestChangesView"]


class CreateBranchView(ProblemObjectView):
    def get(self, request, *args, **kwargs):
        form = BranchCreationForm(problem=self.problem)
        return render(request, "problems/create_branch.html", {
            "form": form
        })

    def post(self, request, *args, **kwargs):
        form = BranchCreationForm(request.POST, problem=self.problem)
        if form.is_valid():
            branch = form.save()
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": branch.get_slug(),
            }))
        return render(request, "problems/create_branch.html", {
            "form": form
        })


class BranchControlView(ProblemObjectView):
    def dispatch(self, *args, **kwargs):
        if self.branch is None:
            raise Http404
        else:
            return super(BranchControlView, self).dispatch(*args, **kwargs)


def assert_no_working_copy(func):
    def wrapper(self, request, *args, **kwargs):
        if self.branch.has_working_copy():
            messages.error(
                request,
                _("Pull failed. {user} is working on this branch.").format(
                    user=self.branch.working_copy.author
                )
            )
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug,
            }))
        else:
            return func(self, request, *args, **kwargs)

    return wrapper


class PullBranchView(BranchControlView):

    @assert_no_working_copy
    def get(self, request, *args, **kwargs):
        form = ChooseBranchForm(problem=self.problem)
        return render(request, "problems/pull_branch.html", {
            "form": form,
        })

    @assert_no_working_copy
    def post(self, request, *args, **kwargs):
        form = ChooseBranchForm(request.POST, problem=self.problem)
        if form.is_valid():
            self.branch.merge(form.cleaned_data["source_branch"].head)
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.branch.get_slug(),
            }))
        return render(request, "problems/pull_branch.html", {
            "form":form
        })


class CreateWorkingCopy(BranchControlView):

    @assert_no_working_copy
    def post(self, request, problem_id, revision_slug):

        self.branch.get_or_create_working_copy(request.user)
        messages.success(request, _("Successfully locked branch. "
                                    "Others will not be able to change this branch "
                                    "until you commit or discard your changes."))
        return HttpResponseRedirect(reverse("problems:overview", kwargs={
            "problem_id": self.problem.id,
            "revision_slug": self.branch.get_slug()
        }))


class CommitWorkingCopy(BranchControlView):

    def post(self, request, problem_id, revision_slug):
        if self.branch.has_working_copy():
            commit_form = CommitForm(request.POST, instance=self.branch.working_copy)
            if commit_form.is_valid():
                commit_form.save()
                self.branch.set_working_copy_as_head()
                messages.success(request, _("Committed successfully"))
                return HttpResponseRedirect(reverse("problems:overview", kwargs={
                    "problem_id": self.problem.id,
                    "revision_slug": self.branch.get_slug()
                }))
            else:
                return render(request, "problems/confirm_commit.html", context={
                    "commit_form":commit_form
                })

        else:
            messages.error(request, _("Nothing to commit"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                    "problem_id": self.problem.id,
                    "revision_slug": self.revision_slug,
                }))

    def get(self, request, problem_id, revision_slug):
        if not self.branch.has_working_copy():
            messages.error(request, _("Nothing to commit"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug,
            }))
        commit_form = CommitForm(instance=self.branch.working_copy)

        # TODO: Optimize the process of calculating changes

        changes = get_revision_difference(self.branch.head, self.revision)

        return render(request, "problems/confirm_commit.html", context={
            "changes": changes,
            "commit_form": commit_form
        })


class ConflictsListView(BranchControlView):

    def get(self, request, problem_id, revision_slug):
        if not self.revision.has_merge_result():
            raise Http404
        return render(request, "problems/conflicts.html", context={
            "conflicts": self.revision.merge_result.conflicts.all()
        })


class ResolveConflictView(BranchControlView):

    def post(self, request, problem_id, revision_slug, conflict_id):
        conflict = get_object_or_404(
            Conflict,
            id=conflict_id,
            merge__merged_revision=self.revision,
            resolved=False
        )
        conflict.resolved = True
        conflict.save()
        return HttpResponseRedirect(reverse("problems:conflicts", kwargs={
            "problem_id": self.problem.id,
            "revision_slug": self.revision_slug
        }))

    def get(self, request, problem_id, revision_slug, conflict_id):
        conflict = get_object_or_404(
            Conflict,
            id=conflict_id,
            merge__merged_revision=self.revision,
            resolved=False
        )
        base_object = conflict.theirs
        new_object = conflict.current
        base_dict = base_object.get_value_as_dict() if base_object is not None else {}
        new_dict = new_object.get_value_as_dict() if new_object is not None else {}
        return render(request, "problems/show_conflict_diff.html", context={
            "conflict": conflict,
            "current_with_master_diff": diff_dict(base_dict, new_dict)
        })


class CreateMergeRequest(BranchControlView):

    def get(self, request, *args, **kwargs):
        differences = get_revision_difference(
            base=self.problem.get_master_branch().head,
            new=self.revision
        )
        form = MergeRequestAddForm()
        return render(request, "problems/create_merge_request.html", context={
            "differences": differences,
            "form": form
        })

    def post(self, request, *args, **kwargs):
        form = MergeRequestAddForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            first_comment = form.cleaned_data["description"]
            merge_request = MergeRequest.objects.create(
                problem=self.problem,
                title=title,
                source_branch=self.branch,
                destination_branch=self.problem.get_master_branch(),
                requester=self.request.user,
            )
            merge_request.participants.add(self.request.user)
            comment = Comment.objects.create(
                topic=merge_request,
                author=self.request.user,
                text=first_comment,
            )
            return HttpResponseRedirect(reverse("problems:merge_request", kwargs={
                "problem_id": self.problem.id,
                "merge_request_id": merge_request.id,
                "revision_slug": self.revision_slug,
            }))
        else:
            differences = get_revision_difference(
                base=self.problem.get_master_branch().head,
                new=self.revision
            )
            return render(request, "problems/create_merge_request.html", context={
                "differences": differences,
                "form": form,
            })


class MergeRequestList(ProblemObjectView):

    def get(self, request, *args, **kwargs):
        show_closed = request.GET.get("closed", 0) == "1"
        merge_requests = MergeRequest.objects.filter(source_branch__problem=self.problem)
        if not show_closed:
            merge_requests = merge_requests.filter(status=MergeRequest.OPEN)
        return render(request, "problems/merge_requests_list.html", context={
            "show_closed": show_closed,
            "merge_requests": merge_requests
        })


class MergeRequestDiscussionView(ProblemObjectView):

    def get(self, request, problem_id, revision_slug, merge_request_id):
        merge_request = get_object_or_404(
            MergeRequest,
            source_branch__problem_id=problem_id,
            id=merge_request_id,
        )
        form = CommentAddForm(owner=self.request.user,
                              topic=merge_request)
        return render(request, "problems/merge_request_discussion.html", context={
            "merge_request": merge_request,
            "comment_form": form,
        })

    def post(self, request, problem_id, revision_slug, merge_request_id):

        def redirect_to_current_url():
            return HttpResponseRedirect(reverse("problems:merge_request", kwargs={
                "problem_id": problem_id,
                "revision_slug": revision_slug,
                "merge_request_id": merge_request_id,
            }))

        merge_request = get_object_or_404(
            MergeRequest,
            source_branch__problem_id=problem_id,
            id=merge_request_id,
        )
        if merge_request.status != MergeRequest.OPEN:
            messages.error(request, _("This merge request has already been either closed or merged"))
            return redirect_to_current_url()
        elif request.POST.get("close", None):
            merge_request.close(request.user)
            return redirect_to_current_url()
        elif request.POST.get("merge", None):
            possibility, message = merge_request.can_be_merged()
            if possibility:
                merge_request.merge(request.user)
            else:
                messages.error(request, message)
            return redirect_to_current_url()
        else:
            form = CommentAddForm(request.POST,
                                  owner=self.request.user,
                                  topic=merge_request)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse("problems:merge_request", kwargs={
                    "problem_id": problem_id,
                    "revision_slug": merge_request.destination_branch.get_slug(),
                    "merge_request_id": merge_request_id,
                }))
            return render(request, "problems/merge_request_discussion.html", context={
                "merge_request": merge_request,
                "comment_form": form,
            })


class MergeRequestChangesView(ProblemObjectView):
    def get(self, request, problem_id, revision_slug, merge_request_id):
        merge_request = get_object_or_404(
            MergeRequest,
            source_branch__problem_id=problem_id,
            id=merge_request_id,
        )
        differences = get_revision_difference(
            base=merge_request.destination_branch.head,
            new=merge_request.source_branch.head,
        )
        return render(request, "problems/merge_request_changes.html", context={
            "merge_request": merge_request,
            "differences": differences,
        })