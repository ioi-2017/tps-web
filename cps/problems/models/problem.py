# Amir Keivan Mohtashami
# Mohammad Javad Naderi
import hashlib

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_clone.clone import Cloner

from problems.models import RevisionObject, Conflict, Merge

import logging


__all__ = ["Problem", "ProblemRevision", "ProblemData", "ProblemFork"]

logger = logging.getLogger(__name__)


class Problem(models.Model):
    master_revision = models.ForeignKey("ProblemRevision", verbose_name=_("master revision"), related_name='+',
                                        null=True, blank=True)
    users = models.ManyToManyField("accounts.User", through='accounts.UserProblem', related_name='problems')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("creator"))
    creation_date = models.DateTimeField(verbose_name=_("creation date"), auto_now_add=True)

    def get_upstream_fork(self):
        return self.forks.get(owner=None)

    def get_or_create_fork(self, user):
        # TODO: Maybe check permissions here
        try:
            return self.forks.get(owner=user)
        except ProblemFork.DoesNotExist:
            master_fork = self.get_main_fork()
            master_fork.id = None
            master_fork.owner = user
            master_fork.save()


class ProblemFork(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("fork owner"), null=True, blank=True, db_index=True)
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), db_index=True, related_name="forks")
    head = models.ForeignKey("ProblemRevision", verbose_name=_("head"), null=True, blank=True)

    class Meta:
        unique_together = (("owner", "problem"), )

    def get_editable_head(self):
        if self.head.committed():
            # TODO: Implement lock
            #self.head = clone(self.head)
            self.save()
        return self.head


class ProblemRevision(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("revision owner"))
    fork = models.ForeignKey(ProblemFork, verbose_name=_("fork"), db_index=True, related_name="revisions")
    revision_id = models.CharField(verbose_name=_("revision id"), max_length=40, null=True, blank=True, editable=False,
                                   db_index=True, unique=True)
    parent_revision = models.ForeignKey("ProblemRevision", verbose_name=_("parent revision"), null=True, blank=True, related_name='+')
    depth = models.IntegerField(verbose_name=_("revision depth"), blank=True)

    def commit(self):
        self.revision_id = hashlib.sha1((str(self.id) + settings.SECRET_KEY).encode("utf-8")).hexdigest()
        self.save()

    def committed(self):
        return self.revision_id is not None

    @property
    def problem(self):
        return self.fork.problem

    def save(self, *args, **kwargs):
        if self.parent_revision:
            self.depth = self.parent_revision.depth + 1
        else:
            self.depth = 1
        super(ProblemRevision, self).save(*args, **kwargs)

    @staticmethod
    def _get_cloner():
        return Cloner(blocking_models=["file_repository.FileModel"],
                      ignored_models=["file_repository.FileModel"],
                      ignored_fields=[("problems.ProblemRevision", "parent_revision"),
                                      ("problems.ProblemRevision", "fork"),
                                      ("problems.ProblemRevision", "author")],)

    def clone(self):
        self.revision_id = None
        cloned = self._get_cloner().clone(self)[0]
        cloned.revision_id = None
        cloned.parent_revision = self
        cloned.save()
        return cloned

    def find_merge_base(self, another_revision):
        revision_a = self
        revision_b = another_revision
        while revision_a is not None and revision_b is not None and revision_a.pk != revision_b.pk:
            if revision_a.pk > revision_b.pk:
                revision_a = revision_a.parent_revision
            else:
                revision_b = revision_b.parent_revision
        if revision_a.pk == revision_b.pk:
            return revision_a

    def find_matching_pairs(self, another_revision):
        attributes = {
            "testcase_set", "solution_set", "validator_set", "sourcefile_set",
            "attachment_set", "solutionrun_set", "subtasks"
        }
        res = [(self.problem_data.all()[0], another_revision.problem_data.all()[0])]
        for attr in attributes:
            res = res + getattr(self, attr).find_matches(getattr(another_revision, attr))
        return res

    def merge(self, another_revision):
        if not self.committed():
            raise AssertionError("Commit changes before merge")

        merge_base = self.find_merge_base(another_revision)
        base_current = merge_base.find_matching_pairs(self)
        base_other = merge_base.find_matching_pairs(another_revision)
        current_other = self.find_matching_pairs(another_revision)
        base_current_dict = {a: b for a, b in base_current if a is not None}
        current_base_dict = {b: a for a, b in base_current if b is not None}
        base_other_dict = {a: b for a, b in base_other if a is not None}
        other_base_dict = {b: a for a, b in base_other if b is not None}

        matched_triples = []
        for a, b in base_current_dict.items():
            matched_triples.append((a, b, base_other_dict.get(a, None)))
        for a, b in base_other_dict.items():
            if base_current_dict.get(a, None) is None:
                matched_triples.append((a, None, b))
        for a, b in current_other:
            if current_base_dict.get(a, None) is None and other_base_dict.get(b, None) is None:
                matched_triples.append((None, a, b))

        ours_ignored = []
        theirs_ignored = {}
        conflicts = []

        for base, ours, theirs in matched_triples:
            not_none_object = next(a for a in [base, ours, theirs] if a is not None)
            base_ours = not_none_object.differ(base, ours)
            base_theirs = not_none_object.differ(base, theirs)
            ours_theirs = not_none_object.differ(ours, theirs)

            if ours_theirs:
                if base_ours:
                    if base_theirs:
                        conflicts.append((ours, theirs))
                    if theirs is not None:
                        theirs_ignored[theirs] = ours
                else:
                    if ours is not None:
                        ours_ignored.append(ours)
            else:
                if ours is not None:
                    ours_ignored.append(ours)

        new_revision = self.clone()
        merge = Merge.objects.create(merged_revision=new_revision,
                                     our_revision=self,
                                     their_revision=another_revision,
                                     base_revision=merge_base)
        current_new = self.find_matching_pairs(new_revision)
        current_new_dict = {a: b for a, b in current_new if a is not None}
        for obj in ours_ignored:
            new_obj = current_new_dict[obj]
            try:
                new_obj.delete()
            except Exception as e:
                logger.error(e)
                # if the remove fails (possibly due to
                # previous removal caused by cascades)
                # we ignore it
                pass

        theirs_ignored[another_revision] = new_revision
        self._get_cloner().apply_limits(ignored_instances=theirs_ignored).clone(another_revision)

        for ours, theirs in conflicts:
            current = current_new_dict[ours]
            Conflict.objects.create(merge=merge, ours=ours, theirs=theirs, current=current)



class ProblemData(RevisionObject):
    problem = models.ForeignKey(ProblemRevision, related_name='problem_data')
    code_name = models.CharField(verbose_name=_("code name"), max_length=150, db_index=True)
    title = models.CharField(verbose_name=_("title"), max_length=150)

    task_type = models.CharField(verbose_name=_("task type"), max_length=150, null=True)
    task_type_parameters = models.TextField(verbose_name=_("task type parameters"), null=True)

    score_type = models.CharField(verbose_name=_("score type"), max_length=150, null=True)
    score_type_parameters = models.TextField(verbose_name=_("score type parameters"), null=True)

    checker = models.ForeignKey("SourceFile", verbose_name=_("checker"), on_delete=models.SET_NULL, null=True, blank=True)

    time_limit = models.FloatField(verbose_name=_("time limt"), help_text=_("in seconds"), default=2)
    memory_limit = models.IntegerField(verbose_name=_("memory limit"), help_text=_("in megabytes"), default=256)
