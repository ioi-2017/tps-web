from django.contrib.auth.models import AbstractUser, Permission
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.conf import settings


__all__ = ["ProblemRole", "ProblemUserRole"]


class ProblemRole(models.Model):
    name = models.CharField(max_length=40, verbose_name=_("role name"))
    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("permissions"),
        limit_choices_to={"content_type__app_label": "problems"},
        related_name="granted_roles"
    )

    def __str__(self):
        return self.name


class ProblemUserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), related_name="problem_roles")
    problem = models.ForeignKey("problems.Problem", verbose_name=_("problem"), related_name="contributors_roles")
    role = models.ForeignKey(ProblemRole, verbose_name=_("role"))

    class Meta:
        unique_together = (('user', 'problem',),)

    def __str__(self):
        return "{user} as {role} in {problem}".format(
            user=str(self.user),
            role=str(self.role),
            problem=str(self.problem)
        )
