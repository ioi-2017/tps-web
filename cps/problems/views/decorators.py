from problems.models import Problem


def authenticate_problem_access(required_permissions):
    if not isinstance(required_permissions, (list, tuple)):
        required_permissions = [required_permissions]
    def wrap(func):
        def wrapper(self, request, *args, **kwargs):

            problem = Problem.objects.get(id=kwargs.pop("problem_id"))
            revision_id = kwargs.pop("revision_id", None)
            if revision_id:
                revision = problem.problemrevision_set.get(id=revision_id)
            else:
                revision = problem.master_revision

            return func(self, request, problem, revision, *args, **kwargs)

        return wrapper
    return wrap