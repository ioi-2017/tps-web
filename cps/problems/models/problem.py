# Amir Keivan Mohtashami
# Mohammad Javad Naderi
import hashlib


from django.conf import settings
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django_clone.clone import Cloner

from problems.models import RevisionObject, Conflict, Merge

import logging


__all__ = ["Problem", "ProblemRevision", "ProblemData", "ProblemFork"]

logger = logging.getLogger(__name__)


class Problem(models.Model):

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
            with transaction.atomic():
                master_fork = self.get_upstream_fork()
                master_fork.id = None
                master_fork.owner = user
                master_fork.save()
                return master_fork

    def __str__(self):
        return str(self.pk)


class ProblemFork(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("fork owner"), null=True, blank=True, db_index=True)
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), db_index=True, related_name="forks")
    head = models.ForeignKey("ProblemRevision", verbose_name=_("head"), related_name='+')
    working_copy = models.OneToOneField("ProblemRevision", verbose_name=_("working copy"), related_name='+', null=True)

    class Meta:
        unique_together = (("owner", "problem"), )

    def has_working_copy(self):
        if self.working_copy is not None and self.working_copy.committed():
            self.working_copy = None
        return self.working_copy is not None

    def get_slug(self):
        if self.owner:
            return self.owner.username
        else:
            return "master"

    def discard_working_copy(self, commit=True):
        self.working_copy = None
        if commit:
            self.save()

    def get_or_create_working_copy(self, user):
        if not self.has_working_copy():
            self.working_copy = self.head.clone()
            self.working_copy.author = user
            self.save()
        return self.working_copy

    def get_working_copy_or_head(self):
        if self.has_working_copy():
            return self.working_copy
        else:
            return self.head

    def set_as_head(self, revision, commit=True):
        # TODO: Maybe we can assert that head is a parent of this revision
        # TODO: The question is do we really want it?
        self.head = revision
        if commit:
            self.save()

    def set_working_copy_as_head(self):
        self.set_as_head(self.working_copy, commit=False)
        self.discard_working_copy(commit=False)
        self.save()

    def __str__(self):
        return str(self.problem) + ": " + str(self.owner)

    def merge(self, another_revision):
        self.working_copy = self.head.merge(another_revision)
        self.save()


class ProblemRevision(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("revision owner"))
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), db_index=True, related_name="revisions")
    revision_id = models.CharField(verbose_name=_("revision id"), max_length=40, null=True, blank=True, editable=False,
                                   db_index=True, unique=True)
    commit_message = models.TextField(verbose_name=_("commit message"), blank=False)
    parent_revisions = models.ManyToManyField("ProblemRevision", verbose_name=_("parent revisions"), related_name='+')
    depth = models.IntegerField(verbose_name=_("revision depth"), blank=True)

    def __str__(self):
        return "{} - {}: {}({})".format(self.problem, self.author, self.revision_id, self.pk)

    def commit(self, message):
        self.commit_message = message
        self.revision_id = hashlib.sha1((str(self.id) + settings.SECRET_KEY).encode("utf-8")).hexdigest()
        self.save()

    def committed(self):
        return self.revision_id is not None

    @property
    def problem_data(self):
        return self.problemdata_set.all()[0]

    def editable(self, user):
        return not self.committed() and self.author == user

    def save(self, *args, **kwargs):
        self.depth = 1
        super(ProblemRevision, self).save(*args, **kwargs)
        for parent in self.parent_revisions.all():
            self.depth = max(self.depth, parent.depth + 1)
        super(ProblemRevision, self).save()

    def _clean_commit_data(self, commit=True):
        self.revision_id = None
        self.commit_message = ""
        if commit:
            self.save()

    @staticmethod
    def _get_cloner():
        return Cloner(blocking_models=["file_repository.FileModel"],
                      ignored_models=["file_repository.FileModel"],
                      ignored_fields=[("problems.ProblemRevision", "parent_revisions"),
                                      ("problems.ProblemRevision", "problem"),
                                      ("problems.ProblemRevision", "author"),
                                      ("problems.ProblemRevision", "merge_result")],)

    def clone(self):
        with transaction.atomic():
            # TODO: This is a hack to handle uniqueness of revision id.
            # TODO: Find some other way to handle it properly.
            self.revision_id = None
            cloned = self._get_cloner().clone(self)[0]
            cloned._clean_commit_data(commit=False)
            cloned.parent_revisions = [self]
            cloned.save()
        return cloned

    def child_of(self, revision):
        return self.find_merge_base(revision) == revision

    def has_merge_result(self):
        try:
            merge_result = self.merge_result
        except Merge.DoesNotExist:
            return False
        return True

    def has_unresolved_conflicts(self):
        if self.has_merge_result():
            return self.merge_result.conflicts.filter(resolved=False).count() > 0
        else:
            return False

    def find_merge_base(self, another_revision):
        import heapq
        priority_queue = []
        revision_a = self
        revision_b = another_revision
        heapq.heappush(priority_queue, (-revision_a.pk, revision_a))
        heapq.heappush(priority_queue, (-revision_b.pk, revision_b))
        marks = {}
        marks[revision_a.pk] = 1
        marks[revision_b.pk] = 2
        while len(priority_queue) > 0:
            revision = heapq.heappop(priority_queue)[1]
            if marks[revision.pk] == 3:
                return revision
            for parent_revision in revision.parent_revisions.all():
                if parent_revision.pk not in marks:
                    marks[parent_revision.pk] = 0
                    heapq.heappush(priority_queue, (-parent_revision.pk, parent_revision))
                marks[parent_revision.pk] |= marks[revision.pk]
        return None

    def find_matching_pairs(self, another_revision):
        attributes = {
            "testcase_set", "solution_set", "validator_set", "sourcefile_set",
            "attachment_set", "solutionrun_set", "subtasks"
        }
        res = [(self.problem_data, another_revision.problem_data)]
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
        with transaction.atomic():
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
                if ours is None:
                    current = None
                else:
                    current = current_new_dict[ours]
                Conflict.objects.create(merge=merge, ours=ours, theirs=theirs, current=current)
            new_revision.parent_revisions = [self, another_revision]
            new_revision.save()
            return new_revision


class ProblemData(RevisionObject):
    problem = models.ForeignKey(ProblemRevision)
    code_name = models.CharField(verbose_name=_("code name"), max_length=150, db_index=True)
    title = models.CharField(verbose_name=_("title"), max_length=150)

    task_type = models.CharField(verbose_name=_("task type"), max_length=150, null=True)
    task_type_parameters = models.TextField(verbose_name=_("task type parameters"), null=True)

    score_type = models.CharField(verbose_name=_("score type"), max_length=150, null=True)
    score_type_parameters = models.TextField(verbose_name=_("score type parameters"), null=True)

    checker = models.ForeignKey("SourceFile", verbose_name=_("checker"), on_delete=models.SET_NULL, null=True, blank=True)

    time_limit = models.FloatField(verbose_name=_("time limt"), help_text=_("in seconds"), default=2)
    memory_limit = models.IntegerField(verbose_name=_("memory limit"), help_text=_("in megabytes"), default=256)
