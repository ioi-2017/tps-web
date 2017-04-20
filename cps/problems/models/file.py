# Amir Keivan Mohtashami
# Amirmohsen Ahanchi
import hashlib
import logging

from django.conf import settings

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models.problem import ProblemRevision
from problems.models.version_control import RevisionObject
from runner import RUNNER_SUPPORTED_LANGUAGES as SUPPORTED_SOURCE_LANGUAGES
from runner import get_compilation_commands
from runner.actions.action import ActionDescription
from runner.actions.compile_source import compile_source
from runner.sandbox.sandbox import SandboxInterfaceException
from tasks.tasks import CeleryTask
import os


__all__ = ["Resource", "SourceFile"]

logger = logging.getLogger(__name__)

FileNameValidator = RegexValidator(
    regex=r'^{character}(?:\.|{character})*$'.format(character=r'[a-zA-Z0-9_\-]'),
    message=_("Please enter a valid file name."),
    code='invalid_file_name',
    inverse_match=False
)

def get_valid_name(name):
    initial_prefix = "prefix_"
    valid_name = initial_prefix
    for char in name:
        try:
            FileNameValidator(valid_name + char)
        except ValidationError:
            continue
        valid_name += char
    valid_name = valid_name[len(initial_prefix):]
    if valid_name == "" or valid_name[0] == ".":
        valid_name = "{}".format(hashlib.md5(name.encode()).hexdigest()) + valid_name

    return valid_name


class ResourceBase(RevisionObject):
    problem = models.ForeignKey("ProblemRevision", verbose_name=_("problem"))
    name = models.CharField(max_length=50, verbose_name=_("name"), validators=[FileNameValidator],
                            blank=True, db_index=True)
    file = models.ForeignKey(FileModel, verbose_name=_("file"), related_name="+")

    @staticmethod
    def get_matching_fields():
        return ["name"]

    def get_value_as_dict(self):
        return {"code": self.file.get_value_as_string()}

    class Meta:
        abstract = True
        unique_together = ("problem", "name")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name == "":
            self.name = get_valid_name(self.file.name)

        super(ResourceBase, self).save(*args, **kwargs)


class Resource(ResourceBase):
    pass


# TODO: Source file can have multiple files (e.g. testlib.h)
class SourceFile(ResourceBase):
    source_language = models.CharField(
        choices=[(x, x) for x in SUPPORTED_SOURCE_LANGUAGES],
        max_length=max([200] + [len(language) for language in SUPPORTED_SOURCE_LANGUAGES])
    )

    compiled_file = models.ForeignKey(FileModel, verbose_name=_("compiled file"),
                                      related_name="+", null=True, blank=True)

    compilation_task_id = models.CharField(verbose_name=_("compilation task id"), max_length=128, null=True)
    compilation_finished = models.BooleanField(verbose_name=_("compilation finished"), default=False)

    last_compile_log = models.TextField(verbose_name=_("last compile log"))

    class Meta(ResourceBase.Meta):
        abstract = True

    @property
    def source_file(self):
        # Backward compatibility
        return self.file

    def _compile(self):
        # TODO: Handling of simulataneous compilation of a single source file

        code_name = self.name
        compiled_file_name = self.name + ".out"
        compile_commands = get_compilation_commands(self.source_language, [code_name],
                                                    compiled_file_name)
        files = [(resource.name, resource.file) for resource in self.problem.resource_set.all()]
        files.append((code_name, self.source_file))
        action = ActionDescription(
            commands=compile_commands,
            files=files,
            output_files=[compiled_file_name],
            time_limit=settings.FAILSAFE_TIME_LIMIT,
            memory_limit=settings.FAILSAFE_MEMORY_LIMIT
        )

        success, compilation_success, outputs, stdout, stderr, sandbox_data = compile_source(action)

        self.compiled_file = None

        if not success:
            logger.error("Running compilation command failed due to sandbox error")
        else:
            self.last_compile_log = "Standard output:\n" + stdout + "\n"
            self.last_compile_log += "Standard error:\n" + stderr + "\n"
            if compilation_success:
                self.compiled_file = outputs[compiled_file_name]

        self.compilation_finished = True

        self.save()

    def compilation_started(self):
        return self.compilation_task_id is not None

    def compile(self):
        if not self.compilation_started():
            self.compilation_task_id = CompilationTask().delay(self).id
            self.save()

    def invalidate_compilation(self):
        self.compiled_file = None
        self.last_compile_log = ""
        self.compilation_task_id = None
        self.compilation_finished = False
        self.save()

    def compilation_successful(self):
        return self.compiled_file is not None


class CompilationTask(CeleryTask):

    def execute(self, source_file):
        try:
            source_file._compile()
        except SandboxInterfaceException:
            self.retry(countdown=5)

    def shadow_name(self, args, kwargs, options):
        def get_source_file(source_file, *args, **kwargs):
            return source_file
        source = get_source_file(*args, **kwargs)
        return "Compilation of {source} in {problem}".format(
            problem=str(source.problem),
            source=str(source)
        )