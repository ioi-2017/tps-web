# Amir Keivan Mohtashami
import os

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.fields import EnumField
from file_repository.models import FileModel, GitFile
from problems.models import RevisionObject, CloneableMixin
from problems.models.enums import SolutionVerdict
from problems.models.fields import ReadOnlyGitToGitForeignKey
from problems.models.file import FileNameValidator, get_valid_name
from problems.models.generic import JSONModel
from problems.models.problem import ProblemCommit
from problems.models.testdata import Subtask
from problems.models.version_control import MatchableMixin

from git_orm import models as git_models

__all__ = ["Solution", "SolutionSubtaskExpectedVerdict"]


class SolutionFile(GitFile):

    class Meta:
        storage_name = "solution"


class Solution(JSONModel):
    _VERDICTS = [(x.name, x.value[0]) for x in list(SolutionVerdict)]

    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)
    name = models.CharField(verbose_name=_("name"), validators=[FileNameValidator], max_length=255,
                            blank=True, db_index=True, primary_key=True)
    code = ReadOnlyGitToGitForeignKey(SolutionFile, verbose_name=_("code"), related_name='+', )

    @property
    def get_code_id(self):
        return self.name


    # TODO: Should we validate the language here as well?
    language = models.CharField(verbose_name=_("language"), null=True, max_length=20)
    verdict = EnumField(enum=SolutionVerdict, verbose_name=_("verdict"), max_length=50)

    class Meta:
        unique_together = ("problem", "name",)
        ordering = ("problem", "name", )
        index_together = ("problem", "name",)
        json_db_name = "solutions.json"

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
        if self.language is None:
            return "Auto-detect"
        choices = [(a, a) for a in self.problem.get_judge().get_supported_languages()]
        for repr, val in choices:
            if self.language == val:
                return repr
        return "Not supported"

    def load(self, data, *args, **kwargs):
        data.pop("except", None)
        super(Solution, self).load(data, *args, **kwargs)
        try:
            self.code
        except GitFile.DoesNotExist as e:
            raise self.InvalidObject(e)

    def save(self, *args, **kwargs):
        if self.name == "":
            self.name = get_valid_name(self.code.name)

        super(Solution, self).save(*args, **kwargs)


class SolutionSubtaskExpectedVerdict(models.Model, CloneableMixin, MatchableMixin):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionVerdict)]

    #solution = models.ForeignKey(Solution, verbose_name=_("solution"), related_name="subtask_verdicts")
    #subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    verdict = EnumField(enum=SolutionVerdict, verbose_name=_("verdict"), max_length=50)

    class Meta:
        unique_together = (
      #      ("solution", "subtask")
        )

    def _clean_for_clone(self, cloned_instances):
        super(SolutionSubtaskExpectedVerdict, self)._clean_for_clone(cloned_instances)
        self.solution = cloned_instances[self.solution]
        self.subtask = cloned_instances[self.subtask]

    def get_value_as_dict(self):
        return {
            "solution": str(self.solution),
            "subtask": str(self.subtask),
            "verdict": str(self.verdict)
        }

    def get_match(self, other_revision):
        try:
            other_solution = self.solution.get_match(other_revision)
            if other_solution is None:
                return None
            other_subtask = self.subtask.get_match(other_revision)
            if other_subtask is None:
                return None
            return other_solution.subtask_verdicts.get(subtask=other_subtask)
        except Solution.DoesNotExist:
            return None
        except Subtask.DoesNotExist:
            return None
        except SolutionSubtaskExpectedVerdict.DoesNotExist:
            return None

    def matches_with(self, other_object):
        return \
            self.solution.matches_with(other_object.solution) and \
            self.subtask.matches_with(other_object.subtask)


    def __str__(self):
        return "{solution} on {subtask}".format(solution=self.solution, subtask=self.subtask)
