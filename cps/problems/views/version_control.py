from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.utils.translation import ugettext as _

from problems.forms.version_control import CommitForm
from problems.models import Conflict, ProblemRevision
from problems.views.generics import RevisionObjectView
from problems.views.utils import extract_revision_data

__all__ = ["UpdateForkView", "CommitWorkingCopy",
           "CreateWorkingCopy", "ConflictsListView", "ResolveConflictView",
           "ApplyForkToMaster", "HistoryView"]


class UpdateForkView(View):

    def post(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        if not fork:
            raise Http404
        if fork.has_working_copy():
            messages.error(request, _("A working copy exists. You must commit all changes before updating your fork"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": problem.id,
                "revision_slug": fork.get_slug()
            }))
        fork.merge(problem.get_upstream_fork().head)
        return HttpResponseRedirect(reverse("problems:overview", kwargs={
            "problem_id": problem.id,
            "revision_slug": fork.get_slug()
        }))


class CreateWorkingCopy(View):

    def post(self, request, problem_id, revision_slug):

        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        if not fork:
            raise Http404
        # FIXME: full access is given to superusers.
        # FIXME: This is just for testing purposes and must be removed
        if not request.user.is_superuser and fork.owner != request.user:
            raise PermissionDenied
        if fork.has_working_copy():
            messages.error(request, _("A working copy already exists. You must discard it before creating a new one"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": problem.id,
                "revision_slug": fork.get_slug()
            }))
        else:
            fork.get_or_create_working_copy(request.user)
            messages.success(request, _("Working copy created"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": problem.id,
                "revision_slug": fork.get_slug()
            }))


class CommitWorkingCopy(View):

    def post(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        # FIXME: full access is given to superusers.
        # FIXME: This is just for testing purposes and must be removed
        if not request.user.is_superuser and fork.owner != request.user:
            raise PermissionDenied
        if fork.has_working_copy():
            commit_form = CommitForm(request.POST, instance=fork.working_copy)
            if commit_form.is_valid():
                commit_form.save()
                fork.set_working_copy_as_head()
                messages.success(request, _("Committed successfully"))
                return HttpResponseRedirect(reverse("problems:overview", kwargs={
                    "problem_id": problem.id,
                    "revision_slug": fork.get_slug()
                }))
            else:
                return render(request, "problems/confirm_commit.html", context={
                    "commit_form":commit_form
                })

        else:
            messages.error(request, _("Nothing to commit"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                    "problem_id": problem.id,
                    "revision_slug": fork.get_slug()
                }))

    def get(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        # FIXME: full access is given to superusers.
        # FIXME: This is just for testing purposes and must be removed
        if not request.user.is_superuser and fork.owner != request.user:
            raise PermissionDenied
        if not fork.has_working_copy():
            messages.error(request, _("Nothing to commit"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": problem.id,
                "revision_slug": fork.get_slug()
            }))
        commit_form = CommitForm(instance=fork.working_copy)

        return render(request, "problems/confirm_commit.html", context={
            "commit_form":commit_form
        })


class ConflictsListView(View):

    def get(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        if not revision.has_merge_result():
            raise Http404
        return render(request, "problems/conflicts.html", context={
            "conflicts": revision.merge_result.conflicts.all()
        })


class ResolveConflictView(View):

    def post(self, request, problem_id, revision_slug, conflict_id):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        conflict = get_object_or_404(
            Conflict,
            id=conflict_id,
            merge__merged_revision=revision,
            resolved=False
        )
        conflict.resolved = True
        conflict.save()
        return HttpResponseRedirect(reverse("problems:conflicts", kwargs={
            "problem_id": problem.id,
            "revision_slug": revision_slug
        }))

    def get(self, request, problem_id, revision_slug, conflict_id):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        conflict = get_object_or_404(
            Conflict,
            id=conflict_id,
            merge__merged_revision=revision,
            resolved=False
        )
        return render(request, "problems/show_conflict_diff.html", context={
            "conflict": conflict,
        })


class ApplyForkToMaster(View):

    def post(self, request, problem_id, revision_slug):
        problem, fork, revision = extract_revision_data(problem_id, revision_slug)
        if not fork:
            raise Http404
        master = problem.get_upstream_fork()
        if fork.has_working_copy():
            messages.error(request, _("You must first commit your changes"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": problem.id,
                "revision_slug": fork.get_slug()
            }))
        if not revision.child_of(master.head):
            messages.error(request, _("You must first update your fork"))
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": problem.id,
                "revision_slug": fork.get_slug()
            }))
        master.set_as_head(revision)
        messages.success(request, _("Master updated"))
        return HttpResponseRedirect(reverse("problems:overview", kwargs={
            "problem_id": problem.id,
            "revision_slug": master.get_slug()
        }))


class HistoryView(RevisionObjectView):
    model = ProblemRevision
    template_name = "problems/history.html"

    def get(self, request, *args, **kwargs):

        used = {}
        object_list = [ProblemRevision.objects.get(pk=self.revision.id)]
        i = 0
        while i < len(object_list):
            obj = object_list[i]
            query_set = obj.parent_revisions

            for element in query_set.all():
                if not element.pk in used:
                    object_list.append(element)
                    used[element.pk] = True
            i += 1

        return render(request, self.template_name, context={
            'object_list': sorted(object_list, key=lambda a: a.pk, reverse=True),
        })