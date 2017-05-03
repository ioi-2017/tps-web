# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.fields import EnumField
from file_repository.models import FileModel
from problems.models import RevisionObject, CloneableMixin
from problems.models.enums import SolutionVerdict
from problems.models.file import FileNameValidator, get_valid_name
from problems.models.testdata import Subtask
from problems.models.version_control import MatchableMixin

__all__ = ["Solution", "SolutionSubtaskExpectedVerdict"]


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


class SolutionSubtaskExpectedVerdict(models.Model, CloneableMixin, MatchableMixin):
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

    def get_value_as_dict(self):
        return {
            "solution": str(self.solution),
            "subtask": str(self.subtask),
            "verdict": str(self.verdict)
        }

    def get_match(self, other_revision):
        try:
            other_solution = self.solution.get_match(other_revision)
            other_subtask = self.subtask.get_match(other_revision)
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
