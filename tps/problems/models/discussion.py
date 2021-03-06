
# Amir Keivan Mohtashami
from enum import Enum

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from problems.models.problem import Problem


class Priority(Enum):
    info = "0"
    low = "1"
    medium = "2"
    high = "3"


PRIORITIES = (
    (Priority.info.value, 'info - no effect on correctness '),
    (Priority.low.value, 'low'),
    (Priority.medium.value, 'medium'),
    (Priority.high.value, 'high')
)

__all__ = ["Discussion", "Comment"]


class Discussion(models.Model):
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), related_name='discussions')
    title = models.CharField(max_length=512, verbose_name=_("title"))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("author"))
    start_date = models.DateTimeField(auto_now_add=True, verbose_name=_("posting date"))
    priority = models.CharField(verbose_name=_("priority"), choices=PRIORITIES, max_length=100,
                                default=Priority.medium.value)

    closed = models.BooleanField(verbose_name=_("closed"), default=False)
    comments = GenericRelation(
        "problems.Comment",
        content_type_field="topic_content_type",
        object_id_field="topic_id"
    )

    def last_comment(self):
        return self.comments.latest()


class Comment(models.Model):
    topic_content_type = models.ForeignKey(ContentType, related_name='+')
    topic_id = models.PositiveIntegerField()
    topic = GenericForeignKey("topic_content_type", "topic_id")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("author"))
    text = models.TextField(verbose_name=_("text"))
    posting_date = models.DateTimeField(auto_now_add=True, verbose_name=_("posting date"))
    last_edit = models.DateTimeField(auto_now=True, verbose_name=_("last edit"))

    class Meta:
        get_latest_by = "posting_date"
        ordering = ("topic_content_type", "topic_id", "posting_date", )
