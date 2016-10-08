from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from problems.models import Problem, ProblemRevision


def extract_revision_data(problem_id, revision_slug):
    problem = get_object_or_404(Problem, id=problem_id)
    if revision_slug == "master":

        fork = problem.get_upstream_fork()
        revision = fork.get_working_copy_or_head()
    else:
        try:
            revision = ProblemRevision.objects.get(revision_id=revision_slug,
                                                   problem=problem)
            fork = None
        except ProblemRevision.DoesNotExist:
            try:
                user = get_user_model().objects.get(username=revision_slug)
                fork = problem.get_or_create_fork(user)
                revision = fork.get_working_copy_or_head()
            except ObjectDoesNotExist:
                raise Http404
    return problem, fork, revision


