import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel, GitFile
from problems.models import RevisionObject, ProblemRevision
from problems.models.fields import ReadOnlyGitToGitForeignKey
from problems.models.file import FileNameValidator, get_valid_name
from problems.models.generic import RecursiveDirectoryModel
from problems.models.problem import ProblemCommit

__all__ = ["Grader"]


class GraderFile(GitFile, RecursiveDirectoryModel):

    class Meta:
        storage_name = "grader"


class Grader(RecursiveDirectoryModel):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)
    name = models.CharField(verbose_name=_("name"), validators=[FileNameValidator], max_length=255,
                            blank=True, db_index=True, primary_key=True)
    code = ReadOnlyGitToGitForeignKey(GraderFile, verbose_name=_("code"), related_name='+', )

    @property
    def get_code_id(self):
        return self.name
    language = models.CharField(verbose_name=_("language"), null=True, max_length=20)

    class Meta:
        storage_name = "grader"
        unique_together = ("problem", "name", )
        index_together = ("problem", "name", )

    def __str__(self):
        return self.name

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def load(self, data):
        try:
            self.code
        except GitFile.DoesNotExist as e:
            raise self.InvalidObject(e)

    def get_value_as_dict(self):
        data = dict()
        data["language"] = self.get_language_representation()
        data["code"] = self.code.get_value_as_string()
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

        super(Grader, self).save(*args, **kwargs)
