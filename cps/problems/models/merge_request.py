from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class MergeRequest(models.Model):

    OPEN = "1"
    CLOSED = "2"
    MERGED = "3"
    STATUS_CHOICES = [
        (OPEN, _("open")),
        (CLOSED, _("closed")),
        (MERGED, _("merged")),
    ]
    MERGE_ERROR_MESSAGES = {
        "branch_has_working_copy": _("Someone is still working on branch {branch}."),
        "branch_not_updated": _("Branch {new} is not ahead of {base}. "
                                "It is necessary to pull from {base} and resolve "
                                "possible conflicts before merging {new} into {base}")
    }
    problem = models.ForeignKey("problems.Problem", verbose_name=_("problem"), related_name='merge_requests')
    title = models.CharField(max_length=100)
    source_branch = models.ForeignKey(
        "problems.ProblemBranch",
        verbose_name=_("source branch"),
        related_name='+'
    )
    destination_branch = models.ForeignKey(
        "problems.ProblemBranch",
        verbose_name=_("destination branch"),
        related_name='+'
    )
    status = models.CharField(choices=STATUS_CHOICES, max_length=100, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("requester"), related_name='+')
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_("participants"), related_name='+')
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("closed by"),
        related_name='+',
        null=True, blank=True
    )
    comments = GenericRelation(
        "problems.Comment",
        content_type_field="topic_content_type",
        object_id_field="topic_id"
    )

    class Meta:
        ordering = ("-id", )

    def can_be_merged(self):
        if self.source_branch.has_working_copy():
            return False, self.MERGE_ERROR_MESSAGES["branch_has_working_copy"].format(branch=self.source_branch)
        if self.destination_branch.has_working_copy():
            return False, self.MERGE_ERROR_MESSAGES["branch_has_working_copy"].format(branch=self.destination_branch)
        if not self.source_branch.head.child_of(self.destination_branch.head):
            return False, self.MERGE_ERROR_MESSAGES["branch_not_updated"].format(
                base=self.destination_branch,
                new=self.source_branch
            )
        return True, None

    def merge(self, merger):
        self.status = MergeRequest.MERGED
        self.closed_by = merger
        self.save()
        merge_commit = self.source_branch.head.clone()
        merge_commit.commit(_("Merged {new} into {base} (#{merge_request_id})").format(
            new=self.source_branch,
            base=self.destination_branch,
            merge_request_id=self.id,
        ))
        merge_commit.author = merger
        merge_commit.save()
        self.destination_branch.set_as_head(merge_commit)

    def close(self, closer):
        self.status = MergeRequest.CLOSED
        self.closed_by = closer
        self.save()

    def __str__(self):
        return self.title
