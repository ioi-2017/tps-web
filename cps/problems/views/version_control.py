from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.utils.translation import ugettext as _

from problems.forms.version_control import CommitForm
from problems.models import Conflict, ProblemRevision, SolutionRun
from problems.models.problem_data import ProblemData
from problems.views.generics import RevisionObjectView, ProblemObjectView
from problems.views.utils import extract_revision_data

__all__ = ["HistoryView", "DiffView"]


class HistoryView(ProblemObjectView):

    def get(self, request, *args, **kwargs):
        commit_list = list(self.revision._transaction.walk(reverse=True))
        object_list = []
        if len(commit_list) > 0:
            for i in range(len(commit_list)):
                if i + 1 < len(commit_list):
                    object_list.append((commit_list[i], commit_list[i + 1]))
                else:
                    object_list.append((commit_list[i], None))

        return render(request, "problems/history.html", context={
            'object_list': object_list,
        })


class DiffView(ProblemObjectView):
    def get(self, request, *args, **kwargs):
        other_slug = kwargs.pop("other_slug")
        _, _, other_revision = extract_revision_data(self.problem.code, other_slug, request.user)
        ours_id = self.revision.commit_id
        theirs_id = other_revision.commit_id
        diff = self.revision._transaction.repo.diff(a=theirs_id, b=ours_id).patch
        return render(request, "problems/diff.html", context={
            "ours_id": ours_id,
            "theirs_id": theirs_id,
            "diff": diff
        })
