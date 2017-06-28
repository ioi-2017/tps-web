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
from problems.views.generics import RevisionObjectView
from problems.views.utils import extract_revision_data

__all__ = ["HistoryView"]


class HistoryView(RevisionObjectView):
    model = ProblemRevision
    template_name = "problems/history.html"

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name, context={
            'object_list': self.revision._transaction.walk(reverse=True),
        })
