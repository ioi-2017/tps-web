# Amir Keivan Mohtashami
import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.fields import EnumField
from file_repository.models import FileModel
from problems.models import RevisionObject, CloneableMixin
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

    # TODO: Should we validate the language here as well?
    language = models.CharField(verbose_name=_("language"), null=True, max_length=20)
    verdict = EnumField(enum=SolutionVerdict, verbose_name=_("verdict"), max_length=50)


    class Meta:
        unique_together = ("problem", "name",)
        ordering = ("problem", "name", )

    def __str__(self):
        return self.name

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def get_value_as_dict(self):
        data = {
            "name": self.name,
            "language": self.get_language_representation(),
            "verdict": str(self.verdict),
            "code": self.code.get_value_as_string(),
        }
        return data

    def get_language_representation(self):
        choices = [(a, a) for a in self.problem.get_judge().get_supported_languages()]
        for repr, val in choices:
            if self.language == val:
                return repr
        return "Not supported"

    def save(self, *args, **kwargs):
        if self.name == "":
            self.name = get_valid_name(self.code.name)

        super(Solution, self).save(*args, **kwargs)

    def clone_relations(self, cloned_instances):
        super(Solution, self).clone_relations(cloned_instances)
        CloneableMixin.clone_queryset(self.tests_scores, cloned_instances=cloned_instances)
        CloneableMixin.clone_queryset(self.subtask_verdicts, cloned_instances=cloned_instances)
        CloneableMixin.clone_queryset(self.subtask_scores, cloned_instances=cloned_instances)


class SolutionSubtaskExpectedScore(models.Model, CloneableMixin):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"),related_name="subtask_scores")
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )

    def _clean_for_clone(self, cloned_instances):
        super(SolutionSubtaskExpectedScore, self)._clean_for_clone(cloned_instances)
        self.solution = cloned_instances[self.solution]
        self.subtask = cloned_instances[self.subtask]


class SolutionTestExpectedScore(models.Model, CloneableMixin):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"), related_name="tests_scores")
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "testcase")
        )

    def _clean_for_clone(self, cloned_instances):
        super(SolutionTestExpectedScore, self)._clean_for_clone(cloned_instances)
        self.solution = cloned_instances[self.solution]
        self.testcase = cloned_instances[self.testcase]

class SolutionSubtaskExpectedVerdict(models.Model, CloneableMixin):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionVerdict)]

    solution = models.ForeignKey(Solution, verbose_name=_("solution"), related_name="subtask_verdicts")
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    verdict = EnumField(enum=SolutionVerdict, verbose_name=_("verdict"), max_length=50)

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )

    def _clean_for_clone(self, cloned_instances):
        super(SolutionSubtaskExpectedVerdict, self)._clean_for_clone(cloned_instances)
        self.solution = cloned_instances[self.solution]
        self.subtask = cloned_instances[self.subtask]
