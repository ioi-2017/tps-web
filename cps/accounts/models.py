# Mohammad Javad Naderi
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.db import models


class User(AbstractUser):
    """
    CPS' customized User model
    """
    pass


class Permission(models.Model):
    name = models.CharField(max_length=120, verbose_name=_("permission name"))
    description = models.TextField(blank=True, verbose_name=_("description"))

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=40, verbose_name=_("role name"))
    permissions = models.ManyToManyField(Permission, verbose_name=_("permissions"))

    def __str__(self):
        return self.name


class UserProblem(models.Model):
    """
    Intermediate class between User and Problem.
    """
    user = models.ForeignKey(User, verbose_name=_("user"))
    problem = models.ForeignKey("problems.Problem", verbose_name=_("problem"))
    role = models.ForeignKey(Role, verbose_name=_("role"))

    class Meta:
        unique_together = (('user', 'problem'),)

    def has_permission(self, permission: str):
        """
        :param permission:
        :return: if `user` has permission `permission` for `problem`, return True
        """
        return self.role.permissions.filter(name=permission).exists()
