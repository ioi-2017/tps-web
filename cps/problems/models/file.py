# Amir Keivan Mohtashami
# Amirmohsen Ahanchi

from django.db import models
from file_repository.models import FileModel
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import ProblemRevision
from judge import SUPPORTED_SOURCE_LANGUAGES
from runner import get_compilation_command
from runner.models import JobModel, JobFile
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
        name = self.source_file.name
        compiled_file_name = name + ".out"
        compile_command = get_compilation_command(self.source_language, name,
                                                  compiled_file_name)
        job = JobModel(command=compile_command)
        job.add_file(file_model=self.source_file, filename="input.txt", type=JobFile.READONLY)
        job_file = job.mark_file_for_extraction(filename=compiled_file_name)
        job.run()
        self._compiled_file = job_file.file_model
        self.save()

    def compiled_file(self):
        """
        return compiled_file, if _compiled_file is None it runs compile method to build _compiled_file
        """
        if self._compiled_file is None:
            self.compile()
        return self._compiled_file
