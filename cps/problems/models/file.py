# Amir Keivan Mohtashami

from django.db import models
from file_repository.models import File
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import ProblemRevision
from judge import SUPPORTED_SOURCE_LANGUAGES
from version_control.models import VersionModel


class Attachment(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    file = models.ForeignKey(File, verbose_name=_("file"))


class SourceFile(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    file = models.ForeignKey(File, verbose_name=_("file"))
    source_language = models.CharField(
            choices=SUPPORTED_SOURCE_LANGUAGES,
            null=True,
            max_length=max([200] + [len(language) for language in SUPPORTED_SOURCE_LANGUAGES])
    )