# Amir Keivan Mohtashami
# Amirmohsen Ahanchi

from django.db import models
from file_repository.models import FileModel
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import ProblemRevision
from judge import SUPPORTED_SOURCE_LANGUAGES
from runner import get_compilation_command
from runner.Job import Job
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

        class CompileJob(Job):
            def __init__(self, source_file):
                self.source_file = source_file
                name = self.source_file.source_file.name
                self.compiled_file_name = name + ".out"
                compile_command = get_compilation_command(self.source_file.source_language, name,
                                                          self.compiled_file_name)
                compile_input_files = [(self.source_file.source_file, name)]
                compile_files_to_extract = [self.compiled_file_name]
                super(CompileJob, self).__init__(command=compile_command,
                                                 input_files=compile_input_files,
                                                 files_to_extract=compile_files_to_extract)

            def execute(self):
                super(CompileJob, self).execute()
                self.source_file._compiled_file = self.extracted_files[
                    self.compiled_file_name]
                self.source_file.save()

        compile_job = CompileJob(source_file=self)
        compile_job.run()

    def compiled_file(self):
        """
        return compiled_file, if _compiled_file is None it runs compile method to build _compiled_file
        """
        if self._compiled_file is None:
            self.compile()
        return self._compiled_file
