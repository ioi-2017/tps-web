# Amir Keivan Mohtashami

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from problems.models.problem import Problem

PRIORITIES = (
    ("0", 'info - no effect on correctness '),
    ("1", 'low'),
    ("2", 'medium'),
    ("3", 'high')
)


class Discussion(models.Model):
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), related_name='discussions')
    title = models.CharField(max_length=512, verbose_name=_("title"))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("author"))
    start_date = models.DateTimeField(auto_now_add=True, verbose_name=_("posting date"))
    priority = models.CharField(verbose_name=_("priority"), choices=PRIORITIES, max_length=100)

    def last_comment(self):
        return self.comments.latest()


class Comment(models.Model):
    discussion = models.ForeignKey(Discussion, verbose_name=_("discussion"), related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("author"))
    text = models.TextField(verbose_name=_("text"))
    posting_date = models.DateTimeField(auto_now_add=True, verbose_name=_("posting date"))
    last_edit = models.DateTimeField(auto_now=True, verbose_name=_("last edit"))

    class Meta:
        get_latest_by = "posting_date"