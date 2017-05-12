# Amir Keivan Mohtashami
# Mohammad Javad Naderi
import hashlib
import heapq

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django_clone.clone import Cloner

from file_repository.models import FileModel
from judge import Judge
from problems.models import RevisionObject, Conflict, Merge, CloneableMixin

import logging

from problems.models.enums import SolutionVerdict
from tasks.tasks import CeleryTask

__all__ = ["Problem", "ProblemRevision", "ProblemData", "ProblemBranch"]

logger = logging.getLogger(__name__)


class Problem(models.Model):

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("creator"), related_name='+')
    creation_date = models.DateTimeField(verbose_name=_("creation date"), auto_now_add=True)
    files = models.ManyToManyField(FileModel, verbose_name=_("problem files"))

    def get_master_branch(self):
        return self.branches.get(name="master")

    @staticmethod
    def get_or_create_template_problem():

        if not Problem.objects.filter(pk=0).exists():
            # FIXME: Maybe it would be better to allow null value for creator
            user = get_user_model().objects.filter(is_superuser=True)[0]

            problem = Problem.objects.create(pk=0, creator_id=user.id)
            problem.save()

            problem_revision = ProblemRevision.objects.create(author=user, problem=problem)
            problem_revision.commit("Created problem")
            ProblemBranch.objects.create(
                name="master",
                problem=problem,
                head=problem_revision
            )
            ProblemData.objects.create(
                problem=problem_revision,
                title="BaseProblem",
                code_name="BaseProblem"
            )
        return Problem.objects.get(pk=0)

    @classmethod
    def create_from_template_problem(cls, creator, title, code_name):

        template_problem = cls.get_or_create_template_problem()

        problem = cls.objects.create(creator=creator)

        problem_revision = template_problem.get_master_branch().head.clone()

        problem_data = problem_revision.problem_data
        problem_data.title = title
        problem_data.code_name = code_name
        problem_data.save()

        problem_revision.author = creator
        problem_revision.problem = problem
        problem_revision.parent_revisions.clear()
        problem_revision.commit("Created problem")

        ProblemBranch.objects.create(
            name="master",
            problem=problem,
            head=problem_revision
        )
        return problem

    def __str__(self):
        return "{}(#{})".format(str(self.get_master_branch().head.problem_data.title), str(self.pk))


class ProblemBranch(models.Model):
    name = models.CharField(max_length=30, verbose_name=_("name"), validators=[RegexValidator(r'^\w{1,30}$')])
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("creator"), related_name='+', null=True)
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), db_index=True, related_name="branches")
    head = models.ForeignKey("ProblemRevision", verbose_name=_("head"), related_name='+', on_delete=models.PROTECT)
    working_copy = models.OneToOneField("ProblemRevision", verbose_name=_("working copy"), related_name='+', null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = (("name", "problem"), )
        index_together = (("name", "problem"), )

    def has_working_copy(self):
        if self.working_copy is not None and self.working_copy.committed():
            self.working_copy = None
            self.save()
        return self.working_copy is not None

    def get_slug(self):
        return self.name

    def discard_working_copy(self, commit=True):
        self.working_copy = None
        if commit:
            self.save()

    def get_or_create_working_copy(self, user):
        if not self.editable(user):
            raise AssertionError("This user isn't allowed to "
                                 "create a working copy on this branch")
        self.working_copy = self.head.clone()
        self.working_copy.author = user
        self.working_copy.save()
        self.save()
        return self.working_copy

    def get_branch_revision_for_user(self, user):
        if self.has_working_copy() and self.working_copy.author == user:
            return self.working_copy
        elif self.editable(user):
            return self.get_or_create_working_copy(user)
        else:
            return self.head

    def set_as_head(self, revision, commit=True):
        # TODO: Maybe we can assert that head is a parent of this revision
        # TODO: The question is do we really want it?
        self.head = revision
        if commit:
            self.save()

    def editable(self, user):
        if not user.has_perm("problems.change_problem", obj=self.problem):
            return False
        if self.creator is None:
            return False
        return self.creator == user

    def set_working_copy_as_head(self):
        self.set_as_head(self.working_copy, commit=False)
        self.discard_working_copy(commit=False)
        self.save()

    def __str__(self):
        return self.name

    def pull_from_branch(self, branch):
        self.merge(branch.head)
        if not self.working_copy.has_unresolved_conflicts():
            self.working_copy.commit("Merged with {}".format(branch.name))
            self.set_working_copy_as_head()
            return True
        else:
            return False

    def merge(self, another_revision):
        if self.working_copy_has_changed():
            raise AssertionError("Impossible to merge a revision with a branch with working copy")
        if not another_revision.committed():
            raise AssertionError("Impossible to merge with an uncommitted revision")
        self.working_copy = self.head.merge(another_revision)
        self.save()

    def working_copy_has_changed(self):
        if not self.has_working_copy():
            return False
        return len(self.head.find_differed_pairs(self.working_copy)) > 0


class ProblemJudgeInitialization(CeleryTask):

    def execute(self, problem_revision):
        problem_revision._initialize_in_judge()


class ProblemRevision(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("revision owner"))
    problem = models.ForeignKey(Problem, verbose_name=_("problem"), db_index=True, related_name="revisions")
    revision_id = models.CharField(verbose_name=_("revision id"), max_length=40, null=True, blank=True, editable=False,
                                   db_index=True, unique=True)
    commit_message = models.TextField(verbose_name=_("commit message"), blank=False)
    parent_revisions = models.ManyToManyField("ProblemRevision", verbose_name=_("parent revisions"), related_name='+')
    depth = models.IntegerField(verbose_name=_("revision depth"), blank=True)

    judge_initialization_task_id = models.CharField(verbose_name=_("initialization task id"), max_length=128, null=True)
    judge_initialization_successful = models.NullBooleanField(verbose_name=_("initialization success"))
    judge_initialization_message = models.CharField(verbose_name=_("initialization message"), max_length=256)

    USER_REVISION_OBJECTS = [
        "solution_set", "validator_set", "checker_set", "inputgenerator_set", "grader_set",
        "resource_set", "subtasks", "testcase_set",
    ]

    def get_judge(self):
        return Judge.get_judge()

    def get_task_type(self):
        return self.get_judge().get_task_type(self.problem_data.task_type)

    def _initialize_in_judge(self):
        self.judge_initialization_successful, self.judge_initialization_message = \
            self.get_task_type().initialize_problem(
                problem_code=str(self.pk),
                time_limit=self.problem_data.time_limit,
                memory_limit=self.problem_data.memory_limit,
                task_type_parameters=self.problem_data.task_type_parameters,
                helpers=[
                    (grader.name, grader.code) for grader in self.grader_set.all()
                ],
            )
        self.save()

    def initialize_in_judge(self):
        if not self.judge_initialization_task_id:
            self.judge_initialization_task_id = ProblemJudgeInitialization().delay(self).id
            self.save()

    def invalidate_judge_initialization(self):
        self.judge_initialization_task_id = None
        self.judge_initialization_successful = None
        self.save()

    def judge_initialization_completed(self):
        return self.judge_initialization_successful is not None

    def get_judge_code(self):
        if not self.judge_initialization_successful:
            return None
        else:
            return str(self.pk)

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

    def _clean_for_clone(self, cloned_instances):
        self.revision_id = None
        self.commit_message = ""

    def clone(self, cloned_instances=None, replace_objects=None):
        if not cloned_instances:
            cloned_instances = {}
        if not replace_objects:
            replace_objects = {}
        if self not in cloned_instances:
            cloned_instances[self] = CloneableMixin.clone_model(self, cloned_instances)
        cloned_instances[self].parent_revisions.add(self)
        for queryset in self.USER_REVISION_OBJECTS:
            cloned_instances = CloneableMixin.clone_queryset(getattr(self, queryset),
                                                             cloned_instances=cloned_instances,
                                                             replace_objects=replace_objects)
        for solution in self.solution_set.all():
            for verdict in solution.subtask_verdicts.all():
                verdict.clone(
                    cloned_instances=cloned_instances,
                    replace_objects=replace_objects
                )
        cloned_instances = self.problem_data.clone(
            cloned_instances=cloned_instances,
            replace_objects=replace_objects
        )

        self.problem_data.clone_relations(cloned_instances=cloned_instances)
        for queryset in self.USER_REVISION_OBJECTS:
            CloneableMixin.clone_queryset_relations(getattr(self, queryset),
                                                                       cloned_instances=cloned_instances)

        return cloned_instances[self]

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
        priority_queue = []
        revision_a = self
        revision_b = another_revision
        heapq.heappush(priority_queue, (-revision_a.pk, revision_a))
        heapq.heappush(priority_queue, (-revision_b.pk, revision_b))
        marks = {}
        # Updating mark in the following way to handle
        # the case where both revision are the same
        marks[revision_a.pk] = marks[revision_b.pk] = 0
        marks[revision_a.pk] |= 1
        marks[revision_b.pk] |= 2
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

    def path_to_parent(self, another_revision):
        priority_queue = []
        parents = []
        marks = []
        heapq.heappush(priority_queue, (-self.pk, self))
        marks.append(self.pk)
        while len(priority_queue) > 0:
            revision = heapq.heappop(priority_queue)[1]
            if revision == another_revision:
                break
            for parent_revision in revision.parent_revisions.all():
                if parent_revision.pk not in marks:
                    marks.append(parent_revision.pk)
                    heapq.heappush(priority_queue, (-parent_revision.pk, parent_revision))
            parents.append(revision)
        return parents

    def find_matching_pairs(self, another_revision):
        res = [(self.problem_data, another_revision.problem_data)]
        for attr in self.USER_REVISION_OBJECTS:
            res = res + getattr(self, attr).find_matches(getattr(another_revision, attr))
        for solution in self.solution_set.all():
            for verdict in solution.subtask_verdicts.all():
                res.append((verdict, verdict.get_match(another_revision)))
        for solution in another_revision.solution_set.all():
            for verdict in solution.subtask_verdicts.all():
                if verdict.get_match(self) is None:
                    res.append((None, verdict))
        return res

    def find_differed_pairs(self, another_revision):
        result = []
        for base_object, new_object in self.find_matching_pairs(another_revision):
            not_none_obj = new_object if new_object is not None else base_object
            if not_none_obj.differ(base_object, new_object):
                result.append((base_object, new_object))
        return result

    def merge(self, another_revision):
        if not self.committed():
            raise AssertionError("Commit changes before merge")

        merge_base = self.find_merge_base(another_revision)
        base_current = merge_base.find_matching_pairs(self) if merge_base is not None else {}
        base_other = merge_base.find_matching_pairs(another_revision) if merge_base is not None else {}
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

        ours_ignored = {}
        theirs_ignored = {}
        conflicts = []

        new_revision = self.clone()
        merge = Merge.objects.create(merged_revision=new_revision,
                                     our_revision=self,
                                     their_revision=another_revision,
                                     base_revision=merge_base)
        current_new = self.find_matching_pairs(new_revision)
        current_new_dict = {a: b for a, b in current_new if a is not None}

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
                        theirs_ignored[theirs] = current_new_dict[ours]
                else:
                    if ours is not None:
                        ours_ignored[theirs] = current_new_dict[ours]
            else:
                if ours is not None:
                    ours_ignored[theirs] = current_new_dict[ours]

        theirs_ignored[another_revision] = new_revision

        another_revision.clone(cloned_instances=theirs_ignored, replace_objects=ours_ignored)
        for ours, theirs in conflicts:
            if ours is None:
                current = None
            else:
                current = current_new_dict[ours]
            Conflict.objects.create(merge=merge, ours=ours, theirs=theirs, current=current)
        new_revision.parent_revisions = [self, another_revision]
        new_revision.save()
        return new_revision


class ProblemDataQuerySet(models.QuerySet):

    def find_matches(self, second_queryset, matching_fields=None):

        if isinstance(second_queryset, models.Manager):
            second_queryset = second_queryset.all()

        if len(second_queryset) == 0:
            other = None
        else:
            other = second_queryset[0]

        if len(self.all()) == 0:
            my = None
        else:
            my = self.all()[0]

        return [(my, other)]


class ProblemDataManager(models.Manager):
    use_for_related_fields = True


class ProblemData(RevisionObject):
    problem = models.ForeignKey("problems.ProblemRevision", verbose_name=_("problem"))
    code_name = models.CharField(verbose_name=_("code name"), max_length=150, db_index=True)
    title = models.CharField(verbose_name=_("title"), max_length=150)
    statement = models.TextField(verbose_name=_("statement"), default="", blank=True)

    task_type = models.CharField(verbose_name=_("task type"), max_length=150, null=True)
    task_type_parameters = models.TextField(verbose_name=_("task type parameters"), null=True)

    score_type = models.CharField(verbose_name=_("score type"), max_length=150, null=True)
    score_type_parameters = models.TextField(verbose_name=_("score type parameters"), null=True)

    checker = models.ForeignKey("Checker", verbose_name=_("checker"), on_delete=models.SET_NULL, null=True, blank=True)

    time_limit = models.FloatField(verbose_name=_("time limt"), help_text=_("in seconds"), default=2)
    memory_limit = models.IntegerField(verbose_name=_("memory limit"), help_text=_("in megabytes"), default=256)

    description = models.TextField(verbose_name=_("description"), blank=True)

    objects = ProblemDataManager.from_queryset(ProblemDataQuerySet)()

    @property
    def model_solution(self):
        try:
            return self.problem.solution_set.filter(verdict=SolutionVerdict.model_solution.name)[0]
        except Exception as e:
            return None

    @staticmethod
    def get_matching_fields():
        return []

    def get_value_as_dict(self):
        json_dict = super(ProblemData, self).get_value_as_dict()
        json_dict["checker"] = self.checker.name if self.checker else "None"
        return json_dict

    def __str__(self):
        return self.title

    def _clean_for_clone(self, cloned_instances):
        super(ProblemData, self)._clean_for_clone(cloned_instances)
        if self.checker:
            self.checker = cloned_instances[self.checker]


