from problems.models import ProblemUserRole, Problem

__all__ = ["ProblemRoleBackend", ]


class ProblemRoleBackend(object):

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_active:
            return False
        if not isinstance(obj, Problem):
            return False
        dot_index = perm.find(".")
        if dot_index == -1:
            return False
        app_label, codename = perm[:dot_index], perm[dot_index+1:]
        if app_label != "problems":
            return False

        if obj.creator == user_obj:
            return True
        # TODO: This can be optimized by caching all permissions like Django auth does
        return ProblemUserRole.objects.filter(
            user=user_obj,
            problem=obj,
            role__permissions__codename=codename,
            role__permissions__content_type__app_label=app_label
            # TODO: This can be removed since we only allow problems as app_label
        ).exists()

    def authenticate(self, **credentials):
        """
        We don't want to authenticate any credentials so we simply return None
        """
        return None