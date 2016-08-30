# Amir Keivan Mohtashami
# Mohammad Javad Naderi

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from version_control.models import Revision, VersionModel

__all__= ["Problem", "ProblemRevision", "ProblemData"]


class Problem(models.Model):

    master_revision = models.ForeignKey("ProblemRevision", verbose_name=_("master revision"), related_name='+')
    users = models.ManyToManyField("accounts.User", through='accounts.UserProblem', related_name='problems')


class ProblemRevision(Revision):

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("revision owner"), null=True, blank=True)
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), null=True, blank=True)

    parent_revision = models.ForeignKey("ProblemRevision", verbose_name=_("parent revision"), null=True, blank=True)
    depth = models.IntegerField(verbose_name=_("revision depth"), blank=True)


class ProblemData(VersionModel):

    problem = models.OneToOneField(ProblemRevision, related_name='problem_data')
    code_name = models.CharField(verbose_name=_("code name"), max_length=150, db_index=True)
    title = models.CharField(verbose_name=_("title"), max_length=150)

    task_type = models.CharField(verbose_name=_("task type"), max_length=150, null=True)
    task_type_parameters = models.TextField(verbose_name=_("task type parameters"), null=True)

    score_type = models.CharField(verbose_name=_("score type"), max_length=150, null=True)
    score_type_parameters = models.TextField(verbose_name=_("score type parameters"), null=True)

    checker = models.ForeignKey("SourceFile", verbose_name=_("checker"), null=True, blank=True)

    time_limit = models.FloatField(verbose_name=_("time limt"), help_text=_("in seconds"))
    memory_limit = models.IntegerField(verbose_name=_("memory limit"), help_text=_("in megabytes"))

