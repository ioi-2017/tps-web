from nose.tools import *
from nose.plugins.skip import SkipTest

from git_orm.testcases import GitTestCase
from git_orm import models
from git_orm.models import Q


class Ticket(models.Model):
    title = models.TextField()


class User(models.Model):
    name = models.TextField()


class TestModelBase(GitTestCase):
    def test_exceptions(self):
        for exc_class in models.base.MODEL_EXCEPTIONS:
            model_exc_class = getattr(Ticket, exc_class.__name__)
            ok_(issubclass(model_exc_class, exc_class))

    def test_storage_name(self):
        eq_(Ticket._meta.storage_name, 'tickets')

    def test_objects(self):
        eq_(Ticket.objects.model, Ticket)
        eq_(Ticket.objects.query, Q())

    def test_new(self):
        ticket = Ticket()
        eq_(ticket.title, None)

    def test_equality(self):
        ticket = Ticket()
        ticket2 = Ticket(id=ticket.id)
        eq_(ticket, ticket2)

    def test_equality_unequal(self):
        assert_not_equal(Ticket(), Ticket())

    def test_equality_other_model(self):
        assert_not_equal(Ticket(), User())

    def test_new_with_argument(self):
        ticket = Ticket(title='test ticket')
        eq_(ticket.title, 'test ticket')

    def test_new_with_invalid_argument(self):
        assert_raises(TypeError, Ticket, bar='baz')

    def test_path_with_pk_none(self):
        ticket = Ticket(pk=None)
        assert_raises(ValueError, lambda: ticket.path)

    def test_path(self):
        ticket = Ticket(title='')
        eq_(ticket.path, ['tickets', ticket.id])

    def test_save(self):
        self.assert_commit_count(0)
        ticket = Ticket(title='')
        self.assert_commit_count(0)
        ticket.save()
        # TODO: test validations
        self.assert_commit_count(1)
        self.assert_file_exists('/'.join(ticket.path))

    def test_delete(self):
        raise SkipTest('not implemented yet')

    def test_create(self):
        self.assert_commit_count(0)
        ticket = Ticket.create(title='')
        self.assert_commit_count(1)
        self.assert_file_exists('/'.join(ticket.path))
