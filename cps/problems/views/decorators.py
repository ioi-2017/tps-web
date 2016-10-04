from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from problems.models import Problem, ProblemRevision
from django.contrib.auth import get_user_model

from .utils import extract_revision_data


def problem_view(required_permissions=None):

    def wrap(func):
        def wrapper(self, request, *args, **kwargs):

            problem_id = kwargs.pop("problem_id")
            revision_slug = kwargs.pop("revision_slug")

            problem, revision, fork = extract_revision_data(problem_id, revision_slug)

            return func(self, request, problem, revision, *args, **kwargs)

        return wrapper
    return wrap
