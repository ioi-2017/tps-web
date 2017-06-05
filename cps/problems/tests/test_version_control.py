import tempfile
from django.core.files import File
from django.test import TestCase
from mock import mock
from model_mommy import mommy
from file_repository.models import FileModel
from problems.models import Problem, ProblemRevision, ProblemBranch, Resource, ProblemData, Validator, Subtask


class VersionControlTests(TestCase):
    def setUp(self):
        self.problem = mommy.make(Problem, )
        file = tempfile.NamedTemporaryFile()
        self.file_model = FileModel(file=File(file), name="keyvan")
        self.file_model.save()
        self.base_revision = ProblemRevision.objects.create(
            problem=self.problem,
            author=self.problem.creator
        )

        self.problem_revision1 = ProblemRevision.objects.create(
            problem=self.problem,
            author=self.problem.creator
        )
        self.problem_revision1.parent_revisions.add(self.base_revision)

        self.problem_revision2 = ProblemRevision.objects.create(
            problem=self.problem,
            author=self.problem.creator
        )
        self.problem_revision2.parent_revisions.add(self.base_revision)

        self.problem_branch1 = mommy.make(
            ProblemBranch,
            name="b1",
            problem=self.problem,
            head=self.problem_revision1,
            creator=self.problem.creator,
        )
        self.problem_branch2 = mommy.make(
            ProblemBranch,
            name="b2",
            problem=self.problem,
            head=self.problem_revision2,
            creator=self.problem.creator,
        )

        self.base_revision.commit("Base commit")
        self.problem_revision1.commit("Commit 1")
        self.problem_revision2.commit("Commit 2")

        mommy.make(ProblemData, problem=self.base_revision)
        mommy.make(ProblemData, problem=self.problem_revision1)
        mommy.make(ProblemData, problem=self.problem_revision2)

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_conflicts(self, *args, **kwargs):
        self.create_resource(self.problem_revision1, name="t1")
        self.create_resource(self.problem_revision2, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merge_result.conflicts.all()), 1)
        self.assertEqual(len(new_revision.resource_set.all()), 1)

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_auto_merge(self, *args, **kwargs):
        self.create_resource(self.problem_revision1, name="t1")
        self.create_resource(self.problem_revision2, name="t2")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merge_result.conflicts.all()), 0)
        self.assertEqual(len(new_revision.resource_set.all()), 2)

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=False)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_delete(self, *args, **kwargs):
        self.create_resource(self.base_revision, name="t1")
        self.create_resource(self.problem_revision1, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merge_result.conflicts.all()), 0)
        self.assertEqual(len(new_revision.resource_set.all()), 0)

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_conflict_with_deleted_ours(self, *args, **kwargs):
        self.create_resource(self.base_revision, name="t1")
        self.create_resource(self.problem_revision2, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merge_result.conflicts.all()), 1)
        self.assertEqual(len(new_revision.resource_set.all()), 0)

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_conflict_with_deleted_theirs(self, *args, **kwargs):
        self.create_resource(self.base_revision, name="t1")
        self.create_resource(self.problem_revision1, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merge_result.conflicts.all()), 1)
        self.assertEqual(len(new_revision.resource_set.all()), 1)

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=False)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_fork_merge_with_revision(self, *args, **kwargs):
        fork1_current_head_pk = self.problem_branch1.head.pk
        self.problem_branch1.merge(self.problem_revision2)
        self.assertListEqual(list(self.problem_branch1.working_copy.parent_revisions.all()),
                             [self.problem_revision1, self.problem_revision2])

    @mock.patch("problems.models.file.Resource.diverged_from", return_value=False)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_fork_merge_with_fork(self, *args, **kwargs):
        fork1_current_head_pk = self.problem_branch1.head.pk
        fork2_current_head_pk = self.problem_branch2.head.pk
        self.problem_branch1.merge(self.problem_branch2.head)
        self.assertIsNotNone(self.problem_branch1.working_copy)
        self.assertEqual(fork1_current_head_pk, self.problem_branch1.head.pk)
        self.assertEqual(fork2_current_head_pk, self.problem_branch2.head.pk)

    def create_resource(self, revision, name):
        return Resource.objects.create(problem=revision, name=name, file=self.file_model)

    def test_delete_and_pull(self, *args, **kwargs):
        branch3 = mommy.make(
            ProblemBranch,
            name="b3",
            problem=self.problem,
            head=self.problem_branch1.head,
            creator = self.problem.creator,
        )
        self.problem_branch2.set_as_head(self.problem_branch1.head)
        self.create_resource(self.problem_branch1.head, name="t1")
        working_copy = self.problem_branch2.get_or_create_working_copy(self.problem.creator)
        self.assertEqual(working_copy.resource_set.all().count(), 1)
        working_copy.resource_set.all().delete()
        self.assertEqual(working_copy.resource_set.all().count(), 0)
        working_copy.commit("Deleted")
        self.problem_branch2.set_working_copy_as_head()
        self.assertEqual(self.problem_branch2.head.resource_set.all().count(), 0)
        self.problem_branch1.pull_from_branch(self.problem_branch2)
        self.assertEqual(self.problem_branch1.head.resource_set.all().count(), 0)
        branch3.pull_from_branch(self.problem_branch1)
        self.assertEqual(branch3.head.resource_set.all().count(), 0)


    def test_statement_conflict(self, *args, **kwargs):
        p1 = self.problem_revision1.problem_data
        p1.statement = "P1"
        p1.save()
        p2 = self.problem_revision2.problem_data
        p2.statement = "P2"
        p2.save()
        self.problem_branch1.pull_from_branch(self.problem_branch2)
        revision = self.problem_branch1.working_copy
        self.assertEqual(len(revision.merge_result.conflicts.all()), 1)
        conflict = revision.merge_result.conflicts.get()
        conflict.resolved = True
        conflict.save()
        revision.commit("Resolved")
        self.problem_branch1.set_working_copy_as_head()
        self.problem_branch1.pull_from_branch(self.problem_branch2)

        self.assertIsNone(self.problem_branch1.working_copy)

    def test_validator_subtask_merge1(self, *args, **kwargs):
        self.problem_branch2.set_as_head(self.problem_branch1.head)
        r = self.problem_branch1.head
        s = mommy.make(Subtask, problem=r, name="t")
        v = mommy.make(Validator, problem=r, global_validator=False)
        v._subtasks.add(s)
        r2 = self.problem_branch2.get_or_create_working_copy(self.problem.creator)
        r2.validator_set.all()[0]._subtasks.clear()
        r2.commit("Committed")
        self.problem_branch2.set_working_copy_as_head()
        self.problem_branch2.pull_from_branch(self.problem_branch1)
        self.assertEqual(len(self.problem_branch2.head.validator_set.all()[0].subtasks), 0)

    def test_validator_subtask_merge2(self, *args, **kwargs):
        self.problem_branch2.set_as_head(self.problem_branch1.head)
        r = self.problem_branch1.head
        s = mommy.make(Subtask, problem=r, name="t")
        v = mommy.make(Validator, problem=r, global_validator=False)
        r2 = self.problem_branch2.get_or_create_working_copy(self.problem.creator)
        r2.validator_set.all()[0]._subtasks.add(r2.subtasks.all()[0])
        r2.commit("Committed")
        self.problem_branch2.set_working_copy_as_head()
        self.problem_branch1.pull_from_branch(self.problem_branch2)
        self.assertEqual(len(self.problem_branch1.head.validator_set.all()[0].subtasks), 1)

    def test_validator_subtask_merge3(self, *args, **kwargs):
        self.problem_branch2.set_as_head(self.problem_branch1.head)
        r = self.problem_branch1.head
        s = mommy.make(Subtask, problem=r, name="t")
        v = mommy.make(Validator, problem=r, global_validator=False)
        v._subtasks.add(s)
        r2 = self.problem_branch2.get_or_create_working_copy(self.problem.creator)
        r2.validator_set.all()[0]._subtasks.clear()
        r2.commit("Committed")
        self.problem_branch2.set_working_copy_as_head()
        self.problem_branch1.pull_from_branch(self.problem_branch2)
        self.assertEqual(len(self.problem_branch1.head.validator_set.all()[0].subtasks), 0)


