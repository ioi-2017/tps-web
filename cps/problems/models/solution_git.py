# Amir Keivan Mohtashami

from django.utils.translation import ugettext_lazy as _

from git_orm import models

__all__ = ["GSolution"]


class GSolution(models.Model):
    # _VERDICTS = [(x.name, x.value[0]) for x in list(SolutionVerdict)]

    name = models.TextField(verbose_name=_("name"), primary_key=True)

    # TODO: After GitFileField implementation
    # code = models.models.ForeignKey(FileModel, verbose_name=_("code"), related_name='+')

    # TODO: Should we validate the language here as well?
    language = models.TextField(verbose_name=_("language"))
    verdict = models.TextField(verbose_name=_("verdict"))

    class Meta:
        storage_name = 'code'

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

    def delete(self):
        pass
