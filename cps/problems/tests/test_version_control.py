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
        self.problem_fork1 = mommy.make(ProblemFork, problem=self.problem)
        self.problem_fork2 = mommy.make(ProblemFork, problem=self.problem)
        self.base_revision = ProblemRevision.objects.create(author=self.problem.creator, fork=self.problem_fork1)
        self.problem_revision1 = ProblemRevision.objects.create(
            author=self.problem.creator,
            fork=self.problem_fork1,
            parent_revision=self.base_revision
        )
        self.problem_revision2 = ProblemRevision.objects.create(
            author=self.problem.creator,
            fork=self.problem_fork2,
            parent_revision=self.base_revision
        )
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
        new_revision = self.problem_fork1.revisions.get(revision_id__isnull=True)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 1)
        self.assertEqual(len(new_revision.attachment_set.all()), 1)

    @mock.patch("problems.models.file.Attachment.diverged_from", return_value=True)
    @mock.patch("problems.models.problem.ProblemData.diverged_from", return_value=False)
    def test_auto_merge(self, *args, **kwargs):
        self.create_attachment(self.problem_revision1, name="t1")
        self.create_attachment(self.problem_revision2, name="t2")
        self.problem_revision1.merge(self.problem_revision2)
        new_revision = self.problem_fork1.revisions.get(revision_id__isnull=True)
        self.assertEqual(len(new_revision.merges.all()[0].conflicts.all()), 0)
        self.assertEqual(len(new_revision.attachment_set.all()), 2)

    def create_attachment(self, revision, name):
        return Attachment.objects.create(problem=revision, name=name, file=self.file_model)



