import tempfile
from django.core.files import File
from django.test import TestCase
from mock import mock
from model_mommy import mommy
from file_repository.models import FileModel
from problems.models import Problem, ProblemRevision, ProblemFork, Attachment, ProblemData


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

        self.problem_fork1 = mommy.make(ProblemFork, problem=self.problem, head=self.problem_revision1)
        self.problem_fork2 = mommy.make(ProblemFork, problem=self.problem, head=self.problem_revision2)

        self.base_revision.commit()
        self.problem_revision1.commit()
        self.problem_revision2.commit()

        mommy.make(ProblemData, problem=self.base_revision)
        mommy.make(ProblemData, problem=self.problem_revision1)
        mommy.make(ProblemData, problem=self.problem_revision2)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_conflicts(self, *args, **kwargs):
        self.create_attachment(self.problem_revision1, name="t1")
        self.create_attachment(self.problem_revision2, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 1)
        self.assertEqual(len(new_revision.attachment_set.all()), 1)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_auto_merge(self, *args, **kwargs):
        self.create_attachment(self.problem_revision1, name="t1")
        self.create_attachment(self.problem_revision2, name="t2")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 0)
        self.assertEqual(len(new_revision.attachment_set.all()), 2)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_delete(self, *args, **kwargs):
        self.create_attachment(self.base_revision, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 0)
        self.assertEqual(len(new_revision.attachment_set.all()), 0)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_conflict_with_deleted_ours(self, *args, **kwargs):
        self.create_attachment(self.base_revision, name="t1")
        self.create_attachment(self.problem_revision2, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 1)
        self.assertEqual(len(new_revision.attachment_set.all()), 0)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_conflict_with_deleted_theirs(self, *args, **kwargs):
        self.create_attachment(self.base_revision, name="t1")
        self.create_attachment(self.problem_revision1, name="t1")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem.revisions.get(revision_id__isnull=True, parent_revisions=self.problem_revision1)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 1)
        self.assertEqual(len(new_revision.attachment_set.all()), 1)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=False)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_fork_merge_with_revision(self, *args, **kwargs):
        fork1_current_head_pk = self.problem_fork1.head.pk
        self.problem_fork1.merge(self.problem_revision2)
        self.assertListEqual(list(self.problem_fork1.head.parent_revisions.all()),
                             [self.problem_revision1, self.problem_revision2])

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=False)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_fork_merge_with_fork(self, *args, **kwargs):
        fork1_current_head_pk = self.problem_fork1.head.pk
        fork2_current_head_pk = self.problem_fork2.head.pk
        self.problem_fork1.merge(self.problem_fork2)
        self.assertNotEqual(fork1_current_head_pk, self.problem_fork1.head.pk)
        self.assertEqual(fork2_current_head_pk, self.problem_fork2.head.pk)

    def create_attachment(self, revision, name):
        return Attachment.objects.create(problem=revision, name=name, file=self.file_model)



