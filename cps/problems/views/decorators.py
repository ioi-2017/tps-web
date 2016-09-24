from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from problems.models import Problem, ProblemRevision
from django.contrib.auth import get_user_model


def problem_view(required_permissions=None):

    def wrap(func):
        def wrapper(self, request, *args, **kwargs):

            problem = Problem.objects.get(id=kwargs.pop("problem_id"))
            revision_slug = kwargs.pop("revision_slug")
            if revision_slug == "master":
                revision = problem.master_revision
            else:
                try:
                    revision = ProblemRevision.objects.get(revision_id=revision_slug,
                                                           problem=problem)
                except ProblemRevision.DoesNotExist:
                    try:
                        user = get_user_model().objects.get(username=revision_slug)
                        revision = problem.get_or_create_fork(user).get_editable_head()
                    except ObjectDoesNotExist:
                        raise Http404

            return func(self, request, problem, revision, *args, **kwargs)

        return wrapper
    return wrap