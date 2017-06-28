from file_repository.models import GitBinaryFile
from problems.models import ProblemCommit
from problems.models.fields import ReadOnlyGitToGitForeignKey
from django.utils.translation import ugettext_lazy as _

__all__ = ["StatementAttachment"]


class StatementAttachment(GitBinaryFile):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)

    class Meta:
        storage_name = "statement"

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        ls = super(StatementAttachment, cls)._get_existing_primary_keys(transaction)
        if "index.md" in ls:
            ls.remove("index.md")
        return ls
