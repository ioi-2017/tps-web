import datetime

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _

from problems.forms.discussion import CommentAddForm
from problems.forms.version_control import BranchCreationForm, ChooseBranchForm, CommitForm, MergeRequestAddForm, \
    CommitFormPullChoice
from problems.models import Conflict, Comment, MergeRequest
from problems.views.generics import ProblemObjectView
from problems.views.utils import get_revision_difference, diff_dict
from django.conf import settings

__all__ = ["CreateBranchView", "BranchControlView", "ConflictsListView", "PullBranchView",
           "ResolveConflictView", "CommitWorkingCopy", "DiscardWorkingCopy",
           "CreateMergeRequest", "MergeRequestList", "MergeRequestDiscussionView",
           "MergeRequestChangesView", "MergeRequestReopenView", "UnfollowMergeRequestView", "FollowMergeRequestView",
           "DeleteBranchView", "BranchesListView"]


def branch_pull(request, source, destination):
    pull_result = destination.pull_from_branch(source)
    if pull_result:
        messages.success(request,
                         _("No conflicts occurred when pulling from {}. Committed automatically").format(source.name))
        return True
    else:
        messages.error(request, _("Conflicts occurred when pulling from {}. ").format(source.name))
        return False


def assert_no_open_merge_request(request, problem, revision_slug, source, destination):
    merge_requests = MergeRequest.objects.filter(
        source_branch=source,
        destination_branch=destination,
        status=MergeRequest.OPEN
    )
    if merge_requests.count() > 0:
        merge_request = merge_requests[0]
        messages.error(request, MergeRequest.error_messages["same_open_request_exists"])
        return HttpResponseRedirect(reverse("problems:merge_request", kwargs={
            "problem_id": problem.id,
            "revision_slug": revision_slug,
            "merge_request_id": merge_request.id,
        }))
    else:
        return None





class CreateBranchView(ProblemObjectView):
    def get(self, request, *args, **kwargs):
        form = BranchCreationForm(problem=self.problem, user=request.user)
        return render(request, "problems/create_branch.html", {
            "form": form
        })

    def post(self, request, *args, **kwargs):
        form = BranchCreationForm(request.POST, problem=self.problem, user=request.user)
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
    def dispatch(self, request, *args, **kwargs):
        if self.branch is None or self.branch.creator != request.user:
            raise Http404
        else:
            return super(BranchControlView, self).dispatch(request, *args, **kwargs)


def assert_not_changed_working_copy(func):
    def wrapper(self, request, *args, **kwargs):
        if self.branch.working_copy_has_changed():
            messages.error(
                request,
                _("Commit or discard your changes first.")
            )
            return HttpResponseRedirect(reverse("problems:commit", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug,
            }))
        else:
            return func(self, request, *args, **kwargs)
    return wrapper


class PullBranchView(BranchControlView):

    @assert_not_changed_working_copy
    def get(self, request, *args, **kwargs):
        form = ChooseBranchForm(problem=self.problem)
        return render(request, "problems/pull_branch.html", {
            "form": form,
        })

    @assert_not_changed_working_copy
    def post(self, request, *args, **kwargs):
        form = ChooseBranchForm(request.POST, problem=self.problem)
        if form.is_valid():
            branch_pull(request, source=form.cleaned_data["source_branch"], destination=self.branch)

            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.branch.get_slug(),
            }))
        return render(request, "problems/pull_branch.html", {
            "form": form
        })


class CommitWorkingCopy(BranchControlView):

    def post(self, request, problem_id, revision_slug):
        if settings.DISABLE_BRANCHES:
            commit_form_class = CommitForm
        else:
            commit_form_class = CommitFormPullChoice
        if self.branch.working_copy_has_changed() and self.revision == self.branch.working_copy:
            if self.branch.working_copy.has_unresolved_conflicts():
                messages.error(request, _("You must resolve all conflicts"))
                return HttpResponseRedirect(reverse("problems:conflicts", kwargs={
                    "problem_id": self.problem.id,
                    "revision_slug": self.branch.get_slug()
                }))
            commit_form = commit_form_class(request.POST, instance=self.branch.working_copy)
            if commit_form.is_valid():
                commit_form.save()
                self.branch.set_working_copy_as_head()
                if settings.DISABLE_BRANCHES:
                    if branch_pull(request, source=self.problem.get_master_branch(), destination=self.branch):
                        self.problem.get_master_branch().set_as_head(self.branch.head)
                elif commit_form.cleaned_data["pull_from_master"]:
                    branch_pull(request, source=self.problem.get_master_branch(), destination=self.branch)

                messages.success(request, _("Committed successfully"))

                if "create_merge_request" in request.POST and not settings.DISABLE_BRANCHES:
                    return HttpResponseRedirect(reverse("problems:create_merge_request", kwargs={
                        "problem_id": self.problem.id,
                        "revision_slug": self.branch.get_slug()
                    }))
                else:
                    return HttpResponseRedirect(reverse("problems:overview", kwargs={
                        "problem_id": self.problem.id,
                        "revision_slug": self.branch.get_slug()
                    }))
            else:
                changes = get_revision_difference(self.branch.head, self.revision)
                return render(request, "problems/confirm_commit.html", context={
                    "changes": changes,
                    "commit_form":commit_form
                })

        else:
            messages.error(request, _("Nothing to commit"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                    "problem_id": self.problem.id,
                    "revision_slug": self.revision_slug,
                }))

    def get(self, request, problem_id, revision_slug):
        if settings.DISABLE_BRANCHES:
            commit_form_class = CommitForm
        else:
            commit_form_class = CommitFormPullChoice
        if not self.branch.working_copy_has_changed():
            messages.error(request, _("Nothing to commit"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug,
            }))
        if self.branch.working_copy.has_unresolved_conflicts():
            messages.error(request, _("You must resolve all conflicts"))
            return HttpResponseRedirect(reverse("problems:conflicts", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.branch.get_slug()
            }))
        # TODO: Optimize the process of calculating changes

        changes = get_revision_difference(self.branch.head, self.revision)

        if len(changes) == 1:
            initial_commit_message = changes[0][0]
        else:
            initial_commit_message = ""

        commit_form = commit_form_class(instance=self.branch.working_copy, initial={
            "commit_message": initial_commit_message
        })

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
        master = self.problem.get_master_branch()
        result = assert_no_open_merge_request(
            request,
            self.problem,
            self.revision_slug,
            source=self.branch,
            destination=master
        )
        if result:
            return result
        differences = get_revision_difference(
            base=master.head,
            new=self.revision
        )
        master_merge_base = self.revision.find_merge_base(master.head)
        default_description = "\n".join(
            ["* " + revision.commit_message for revision in
             self.revision.path_to_parent(
                 master_merge_base
             )]
        )

        form = MergeRequestAddForm(initial={
            "title": self.branch.name.replace("_", " ").capitalize(),
            "description": default_description
        })
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


class BranchesListView(ProblemObjectView):
    def get(self, request, *args, **kwargs):
        return render(request, "problems/branches.html", context={
            "all_branches": self.problem.branches.all(),
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
            "is_follow": merge_request.is_participant(request.user),
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


class DiscardWorkingCopy(BranchControlView):
    def get(self, request, *args, **kwargs):
        if self.branch.has_working_copy() and self.revision == self.branch.working_copy:
            changes = get_revision_difference(self.branch.head, self.revision)
            return render(request, "problems/confirm_discard.html", context={
                "changes": changes,
            })
        else:
            messages.error(request, _("Nothing to discard"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug
            }))

    def post(self, request, *args, **kwargs):
        if self.branch.has_working_copy() and self.revision == self.branch.working_copy:
            self.branch.working_copy.delete()
            if settings.DISABLE_BRANCHES:
                self.branch.refresh_from_db()
                new_name = self.branch.name + "_old_" + str(datetime.datetime.now().timestamp());
                self.branch.name = new_name[:30]
                self.branch.save()

            messages.success(request, _("Discarded successfully"))
        else:
            messages.error(request, _("Nothing to discard"))
        return HttpResponseRedirect(reverse("problems:overview", kwargs={
            "problem_id": self.problem.id,
            "revision_slug": self.revision_slug
        }))


class DeleteBranchView(BranchControlView):
    @assert_not_changed_working_copy
    def get(self, request, *args, **kwargs):
        if self.branch == self.problem.get_master_branch():
            messages.error(request, _("Cannot delete master branch"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug
            }))
        diverged_from_master = self.revision.find_merge_base(self.problem.get_master_branch().head) != self.revision
        return render(request, "problems/confirm_delete_branch.html", context={
            "not_merged_changes": diverged_from_master
        })

    @assert_not_changed_working_copy
    def post(self, request, *args, **kwargs):
        if self.branch == self.problem.get_master_branch():
            messages.error(request, _("Cannot delete master branch"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.revision_slug
            }))
        else:
            self.branch.delete()
            messages.success(request, _("Branch deleted successfully"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": self.problem.id,
                "revision_slug": self.problem.get_master_branch().get_slug()
            }))


class MergeRequestActionView(ProblemObjectView):
    def post(self, request, problem_id, revision_slug, merge_request_id):
        merge_request = get_object_or_404(MergeRequest, id=merge_request_id)
        self.action(request, problem_id, revision_slug, merge_request)

        return HttpResponseRedirect(reverse("problems:merge_request", kwargs={
            "problem_id": problem_id,
            "revision_slug": merge_request.destination_branch.get_slug(),
            "merge_request_id": merge_request_id,
            }))

    def action(self, request, problem_id, revision_slug, merge_request):
        pass


class MergeRequestReopenView(MergeRequestActionView):
    def action(self, request, problem_id, revision_slug, merge_request):
        merge_request.reopen(request.user)


class FollowMergeRequestView(MergeRequestActionView):
    def action(self, request, problem_id, revision_slug, merge_request):
        merge_request.follow(request.user)


class UnfollowMergeRequestView(MergeRequestActionView):
    def action(self, request, problem_id, revision_slug, merge_request):
        merge_request.unfollow(request.user)
