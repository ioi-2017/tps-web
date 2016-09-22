# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from problems.models import RevisionObject
from problems.models.file import SourceFile
from problems.models.problem import ProblemRevision
from problems.models.testdata import TestCase, Subtask


__all__ = ["Solution", "SolutionSubtaskExpectedScore", "SolutionTestExpectedScore"]


class Solution(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    code = models.ForeignKey(SourceFile, verbose_name=_("code"))
    tests_scores = models.ManyToManyField(TestCase, through="SolutionTestExpectedScore")
    subtask_scores = models.ManyToManyField(Subtask, through="SolutionSubtaskExpectedScore")


class SolutionSubtaskExpectedScore(RevisionObject):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )


class SolutionTestExpectedScore(RevisionObject):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "testcase")
        )
