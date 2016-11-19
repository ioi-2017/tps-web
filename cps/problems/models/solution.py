# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from judge.results import JudgeVerdict
from problems.models import RevisionObject
from problems.models.problem import ProblemRevision
from problems.models.testdata import TestCase, Subtask
from multiselectfield import MultiSelectField

__all__ = ["Solution", "SolutionSubtaskExpectedScore", "SolutionTestExpectedScore"]




class Solution(RevisionObject):
    _VERDICTS = [(x.name, x.value) for x in list(JudgeVerdict)]
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    code = models.ForeignKey(FileModel, verbose_name=_("code"), related_name='+')
    tests_scores = models.ManyToManyField(TestCase, through="SolutionTestExpectedScore")
    subtask_scores = models.ManyToManyField(Subtask, through="SolutionSubtaskExpectedScore")
    should_be_present_verdicts = MultiSelectField(choices=_VERDICTS, blank=True)
    should_not_be_present_verdicts = MultiSelectField(choices=_VERDICTS, blank=True)

    def __str__(self):
        return self.code.name


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
