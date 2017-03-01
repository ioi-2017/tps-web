import json

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models import RevisionObject, ProblemRevision
from problems.models.file import FileNameValidator, get_valid_name


class Grader(RevisionObject):
    problem = models.ForeignKey("problems.ProblemRevision", verbose_name=_("problem"))
    name = models.CharField(verbose_name=_("name"), validators=[FileNameValidator], max_length=255,
                            blank=True, db_index=True)
    code = models.ForeignKey(FileModel, verbose_name=_("code"), related_name='+')
    language = models.CharField(verbose_name=_("language"), null=True, max_length=20)

    def __str__(self):
        return self.name

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def get_value_as_string(self):
        data = dict()
        data["language"] = self.get_language_representation()
        data["code"] = self.code.read()
        return json.dumps(data)

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
