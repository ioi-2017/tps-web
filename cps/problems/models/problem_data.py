import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from git_orm import models as git_models, GitError
from git_orm import serializer
from problems.models import ProblemCommit, Checker
from problems.models.enums import SolutionVerdict
from problems.models.fields import ReadOnlyGitToGitForeignKey


__all__ = ["ProblemData"]

class ProblemData(git_models.Model):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)
    name = models.CharField(verbose_name=_("code name"), max_length=150, db_index=True)
    title = models.CharField(verbose_name=_("title"), max_length=150)
    statement = models.TextField(verbose_name=_("statement"), default="", blank=True)

    task_type = models.CharField(verbose_name=_("task type"), max_length=150, null=True)
    task_type_parameters = models.TextField(verbose_name=_("task type parameters"), null=True)

    score_type = models.CharField(verbose_name=_("score type"), max_length=150, null=True)
    score_type_parameters = models.TextField(verbose_name=_("score type parameters"), null=True)

    checker = ReadOnlyGitToGitForeignKey("Checker", verbose_name=_("checker"), null=True)

    time_limit = models.FloatField(verbose_name=_("time limt"), help_text=_("in seconds"), default=2)
    memory_limit = models.IntegerField(verbose_name=_("memory limit"), help_text=_("in megabytes"), default=256)

    description = models.TextField(verbose_name=_("description"), blank=True)

    @property
    def code_name(self):
        return self.name

    @property
    def model_solution(self):
        try:
            return self.problem.solution_set.filter(verdict=SolutionVerdict.model_solution.name)[0]
        except Exception as e:
            return None

    @property
    def get_checker_id(self):
        for checker in self.problem.checker_set.all():
            if os.path.splitext(checker.pk)[0] == "checker":
                return checker.pk

    def __str__(self):
        return self.title

    @property
    def path(self):
        return ["problem.json"]

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        return [0]

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = super(ProblemData, cls)._get_instance(transaction, pk)
        try:
            obj.statement = transaction.get_blob(["statement", "index.md"]).decode("utf-8")
        except GitError:
            pass
        return obj

    def load(self, data):
        # FIXME: The type is deprecated. remove this
        if not hasattr(data, 'items'):
            data = serializer.loads(data)
        if "type" in data:
            data["task_type"] = data["type"]
            del data["type"]
        super(ProblemData, self).load(data)
