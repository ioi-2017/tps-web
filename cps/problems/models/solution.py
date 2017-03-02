# Amir Keivan Mohtashami
import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models import RevisionObject
from problems.models.enums import SolutionVerdict
from problems.models.file import FileNameValidator, get_valid_name
from problems.models.problem import ProblemRevision
from problems.models.testdata import TestCase, Subtask

__all__ = ["Solution", "SolutionSubtaskExpectedScore", "SolutionTestExpectedScore", "SolutionSubtaskExpectedVerdict"]


class Solution(RevisionObject):
    _VERDICTS = [(x.name, x.value[0]) for x in list(SolutionVerdict)]

    problem = models.ForeignKey("problems.ProblemRevision", verbose_name=_("problem"))
    name = models.CharField(verbose_name=_("name"), validators=[FileNameValidator], max_length=255,
                            blank=True, db_index=True)
    code = models.ForeignKey(FileModel, verbose_name=_("code"), related_name='+')
    tests_scores = models.ManyToManyField(TestCase, through="SolutionTestExpectedScore", related_name="+")
    subtask_scores = models.ManyToManyField(Subtask, through="SolutionSubtaskExpectedScore", related_name="+")
    subtask_verdict = models.ManyToManyField(Subtask, through="SolutionSubtaskExpectedVerdict", related_name="+")

    # TODO: Should we validate the language here as well?
    language = models.CharField(verbose_name=_("language"), null=True, max_length=20)
    verdict = models.CharField(choices=_VERDICTS, verbose_name=_("verdict"), max_length=50)


    class Meta:
        unique_together = ("problem", "name",)

    def __str__(self):
        return self.name

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def get_value_as_string(self):
        data = {
            "name": self.name,
            "language": self.get_language_representation(),
            "verdict": self.verdict,
            "code": self.code.get_value_as_string(),
        }
        return json.dumps(data)



    def get_language_representation(self):
        choices = [(a, a) for a in self.problem.get_judge().get_supported_languages()]
        for repr, val in choices:
            if self.language == val:
                return repr
        return "Not supported"

    def get_verdict_representation(self):
        verdict = SolutionVerdict.__members__.get(self.verdict, None)
        if verdict:
            return verdict.value
        else:
            return None

    def save(self, *args, **kwargs):
        if self.name == "":
            self.name = get_valid_name(self.code.name)

        super(Solution, self).save(*args, **kwargs)


class SolutionSubtaskExpectedScore(models.Model):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )


class SolutionTestExpectedScore(models.Model):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "testcase")
        )

class SolutionSubtaskExpectedVerdict(models.Model):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionVerdict)]

    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    verdict = models.CharField(choices=_VERDICTS, verbose_name=_("verdict"), max_length=50)

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )
