# Amir Keivan Mohtashami
# Amirmohsen Ahanchi

from django.db import models
from file_repository.models import FileModel
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import ProblemRevision
from judge import SUPPORTED_SOURCE_LANGUAGES
from runner import get_compilation_command
from version_control.models import VersionModel


class Attachment(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    file = models.ForeignKey(FileModel, verbose_name=_("file"))


# TODO: Source file can have multiple files (e.g. testlib.h)
class SourceFile(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    source_file = models.ForeignKey(FileModel, verbose_name=_("source file"), related_name="+")
    source_language = models.CharField(
        choices=SUPPORTED_SOURCE_LANGUAGES,
        null=True,
        max_length=max([200] + [len(language) for language in SUPPORTED_SOURCE_LANGUAGES])
    )

    _compiled_file = models.ForeignKey(FileModel, verbose_name=_("compiled file"),
                                  related_name="+", null=True)

    def compile(self):
        """
        use runner to compile a file and update compiled_file
        """
        name = self.source_file.file.name
        command = get_compilation_command(self.source_language, name, str(name) + ".out")

    def compiled_file(self):
        raise NotImplementedError("This must be implemented")
