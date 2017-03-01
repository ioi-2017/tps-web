from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.utils.translation import ugettext as _

from problems.forms.version_control import CommitForm
from problems.models import Conflict, ProblemRevision, ProblemData, SolutionRun
from problems.views.generics import RevisionObjectView
from problems.views.utils import extract_revision_data

__all__ = ["HistoryView"]


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