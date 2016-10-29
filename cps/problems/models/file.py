# Amir Keivan Mohtashami
# Amirmohsen Ahanchi

import logging

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models.problem import ProblemRevision
from problems.models.version_control import RevisionObject
from runner import RUNNER_SUPPORTED_LANGUAGES as SUPPORTED_SOURCE_LANGUAGES
from runner import get_compilation_commands, get_source_file_name
from runner.actions.action import ActionDescription
from runner.actions.compile_source import compile_source
from tasks.decorators import allow_async_method
from tasks.models import Task

__all__ = ["Attachment", "SourceFile"]

logger = logging.getLogger(__name__)


class Attachment(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=256, verbose_name=_("name"))
    file = models.ForeignKey(FileModel, verbose_name=_("file"))

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def diverged_from(self, other_object):
        return self.file != other_object.file


# TODO: Source file can have multiple files (e.g. testlib.h)
class SourceFile(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(max_length=256, verbose_name=_("name"))
    source_file = models.ForeignKey(FileModel, verbose_name=_("source file"), related_name="+")
    source_language = models.CharField(
        choices=[(x, x) for x in SUPPORTED_SOURCE_LANGUAGES],
        null=True,
        max_length=max([200] + [len(language) for language in SUPPORTED_SOURCE_LANGUAGES])
    )

    _compiled_file = models.ForeignKey(FileModel, verbose_name=_("compiled file"),
                                       related_name="+", null=True, blank=True)

    last_compile_log = models.TextField(verbose_name=_("last compile log"))

    def compile(self):
        # TODO: Abort currently running compile jobs
        compile_job = CompileJob.objects.create(source_file=self)
        compile_job.apply_async()

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


class CompileJob(Task):

    source_file = models.ForeignKey(SourceFile, related_name="compile_jobs")

    def run(self):
        code_name = get_source_file_name(self.source_file.source_language)
        compiled_file_name = "code.out"
        compile_commands = get_compilation_commands(self.source_file.source_language, code_name,
                                                    compiled_file_name)
        action = ActionDescription(
            commands=compile_commands,
            files=[(code_name, self.source_file.source_file)],
            output_files=[compiled_file_name],
            time_limit=settings.DEFAULT_COMPILATION_TIME_LIMIT,
            memory_limit=settings.DEFAULT_COMPILATION_MEMORY_LIMIT
        )

        success, compilation_success, outputs, stdout, stderr, sandbox_data = compile_source(action)

        self.source_file._compiled_file = None

        if not success:
            logger.error("Running compilation command failed due to sandbox error")
        else:
            self.source_file.last_compile_log = "Standard output:\n" + stdout + "\n"
            self.source_file.last_compile_log += "Standard error:\n" + stderr + "\n"
            if compilation_success:
                self.source_file._compiled_file = outputs[compiled_file_name]
        self.source_file.save()