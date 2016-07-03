from django.db import models
from django.utils.translation import ugettext_lazy as _
from problems.models.file import SourceFile
from problems.models.problem import ProblemRevision
from problems.models.testdata import TestCase, Subtask
from version_control.models import VersionModel


class Solution(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    code = models.OneToOneField(SourceFile, verbose_name=_("code"))
    tests_scores = models.ManyToManyField(TestCase, through="SolutionTestScore")
    subtask_scores = models.ManyToManyField(Subtask, through="SolutionSubtaskScore")


class SolutionSubtaskScore(VersionModel):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    score = models.IntegerField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )

class SolutionTestScore(VersionModel):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    score = models.IntegerField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "testcase")
        )
