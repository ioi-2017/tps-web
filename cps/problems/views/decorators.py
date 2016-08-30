from problems.models import Problem


def authenticate_problem_access(required_permissions):
    if not isinstance(required_permissions, (list, tuple)):
        required_permissions = [required_permissions]
    def wrap(func):
        print(required_permissions)
        def wrapper(self, request, *args, **kwargs):

            problem = Problem.objects.get(id=kwargs.pop("problem_id"))
            return func(self, request, problem, *args, **kwargs)

        return wrapper
    return wrap