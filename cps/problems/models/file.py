# Amir Keivan Mohtashami
# Amirmohsen Ahanchi

from django.db import models
from file_repository.models import FileModel
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import ProblemRevision
from runner import RUNNER_SUPPORTED_LANGUAGES as SUPPORTED_SOURCE_LANGUAGES
from runner import get_compilation_command, get_source_file_name
from runner.models import JobModel, JobFile
from version_control.models import VersionModel


__all__ = ["Attachment", "SourceFile"]


class Attachment(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=256, verbose_name=_("name"))
    file = models.ForeignKey(FileModel, verbose_name=_("file"))


# TODO: Source file can have multiple files (e.g. testlib.h)
class SourceFile(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=256, verbose_name=_("name"))
    source_file = models.ForeignKey(FileModel, verbose_name=_("source file"), related_name="+")
    source_language = models.CharField(
        choices=[(x, x) for x in SUPPORTED_SOURCE_LANGUAGES],
        null=True,
        max_length=max([200] + [len(language) for language in SUPPORTED_SOURCE_LANGUAGES])
    )

    _compiled_file = models.ForeignKey(FileModel, verbose_name=_("compiled file"),
                                       related_name="+", null=True, blank=True  )

    def compile(self):
        """
        use runner to compile a file and update compiled_file
        """
        code_name = get_source_file_name(self.source_language)
        compiled_file_name = "code.out"
        compile_command = get_compilation_command(self.source_language, code_name,
                                                  compiled_file_name)
        job = JobModel(command=compile_command, compile_job=True)
        job.save()
        job.add_file(file_model=self.source_file, filename=code_name, type=JobFile.READONLY)
        job_file = job.mark_file_for_extraction(filename=compiled_file_name)
        job.run()
        job_file.refresh_from_db()
        self._compiled_file = job_file.file_model
        self.save()

    def compiled_file(self):
        """
        return compiled_file, if _compiled_file is None it runs compile method to build _compiled_file
        """
        if self._compiled_file is None:
            self.compile()
        return self._compiled_file

    def is_compiled(self):
        return self._compiled_file is not None

    def __str__(self):
        return self.name
