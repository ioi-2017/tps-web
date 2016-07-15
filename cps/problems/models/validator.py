# Amir Keivan Mohtashami

from django.db import models

from problems.models.file import SourceFile
from problems.models.problem import ProblemRevision
from django.utils.translation import ugettext_lazy as _

from problems.models.testdata import Subtask
from version_control.models import VersionModel


class Validator(VersionModel):
    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    code = models.OneToOneField(SourceFile, verbose_name=_("source code"))
    _subtasks = models.ManyToManyField(Subtask, verbose_name=_("subtasks"))
    _validate_all_subtasks = models.BooleanField(
            verbose_name=_("all subtasks"),
            help_text=_("if marked, it validates all subtasks")
    )

    @property
    def subtasks(self):
        if self._validate_all_subtasks:
            return self.problem.subtasks.all()
        else:
            return self._subtasks

    def validate(self, subtasks=None):
        """
        This method is used to validate the testcases in the given subtasks.
        If subtasks is None, it is replaced by self.subtasks
        """
        raise NotImplementedError("This must be implemented")