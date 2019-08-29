from file_repository.models import GitBinaryFile, GitFile
from git_orm import GitError
from problems.models import ProblemCommit
from problems.models.fields import ReadOnlyGitToGitForeignKey
from django.utils.translation import ugettext_lazy as _

__all__ = ["Statement", "StatementAttachment"]


class Statement(GitFile):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)

    class Meta:
        storage_name = "statement"

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        return ["index.md"]

    @classmethod
    def _get_instance(cls, transaction, pk):
        if pk != "index.md":
            raise cls.DoesNotExist(
                'object with pk {} does not exist'.format(pk))
        obj = cls(pk=pk)
        obj._transaction = transaction
        try:
            content = transaction.get_blob(obj.path).decode('utf-8')
        except GitError:
            content = ""
        obj.load(content)
        return obj


class StatementAttachment(GitBinaryFile):
    problem = ReadOnlyGitToGitForeignKey(ProblemCommit, verbose_name=_("problem"), default=0)

    class Meta:
        storage_name = "statement"

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        ls = transaction.list_blobs([cls._meta.storage_name], recursive=True)
        if "index.md" in ls:
            ls.remove("index.md")
        return ls
