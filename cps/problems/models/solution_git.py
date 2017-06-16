# Amir Keivan Mohtashami

from django.utils.translation import ugettext_lazy as _

from file_repository.git_file import GitFile
from git_orm import models

__all__ = ["GSolution"]


class SolutionFile(GitFile):
    name = models.TextField(verbose_name=_("name"), primary_key=True)

    class Meta:
        storage_name = 'solution/sources'


class GSolution(models.Model):
    # _VERDICTS = [(x.name, x.value[0]) for x in list(SolutionVerdict)]

    name = models.TextField(verbose_name=_("name"), primary_key=True)
    # code = models.ForeignKey(SolutionFile, verbose_name=_("code"), null=False)

    # TODO: Should we validate the language here as well?
    language = models.TextField(verbose_name=_("language"))
    verdict = models.TextField(verbose_name=_("verdict"))

    class Meta:
        storage_name = 'code'
        json_db_name = 'solutions.json'

    def __str__(self):
        return self.name

    def get_value_as_dict(self):
        data = {
            "name": self.name,
            "language": self.get_language_representation(),
            "verdict": str(self.verdict),
            "code": None  # TODO: After GitFileField implementation
        }
        return data

    def get_language_representation(self):
        choices = [(a, a) for a in []]
        for repr, val in choices:
            if self.language == val:
                return repr
        return "Not supported"

    def full_clean(self, exclude=None, validate_unique=True):
        pass

    def validate_unique(self, exclude=None):
        pass

    def delete(self):
        pass
