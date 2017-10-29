from nose.tools import *
from mock import Mock, MagicMock, patch

from git_orm.testcases import GitTestCase
from git_orm import models
from git_orm.models import Q
from git_orm.models.queryset import QuerySet


class X(models.Model):
    def __repr__(self):
        return 'x'


class TestRepr(GitTestCase):
    def test_repr(self):
        qs = QuerySet(X)
        qs.REPR_MAXLEN = 2
        for repr_ in ['[]', '[x]', '[x, x]',  '[x, ...]']:
            eq_(repr(qs), repr_)
            X.create()
        qs.REPR_MAXLEN = 3
        eq_(repr(qs), '[x, x, ...]')
        qs.REPR_MAXLEN = 4
        eq_(repr(qs), '[x, x, x, x]')


class TestEq:
    def test_eq(self):
        qs = QuerySet(X)
        eq_(qs, qs)
        eq_(qs, QuerySet(X))
        eq_(qs, qs.all())
        eq_(qs, qs.filter())
        eq_(qs.filter(), qs.all())

    def test_eq_somthing_else(self):
        assert_not_equal(QuerySet(X), None)
        assert_not_equal(QuerySet(X), 'unicode-cat')
        assert_not_equal(QuerySet(X), X)

    def test_eq_other_model(self):
        class Y(models.Model): pass
        assert_not_equal(QuerySet(X), QuerySet(Y))

    def test_eq_other_query(self):
        assert_not_equal(QuerySet(X), QuerySet(X).filter(title='foo'))


class TestOperators:
    def test_or(self):
        qs = QuerySet(X)
        eq_((qs.filter(a=1) | qs.filter(b=2)).query, Q(a=1) | Q(b=2))

    def test_and(self):
        qs = QuerySet(X)
        eq_((qs.filter(a=1) & qs.filter(b=2)).query, Q(a=1, b=2))

    def test_invert(self):
        qs = QuerySet(X)
        eq_(~qs.filter(a=1).query, ~Q(a=1))

    def test_slice(self):
        qs = QuerySet(X)
        eq_(qs[:3].query, Q()[:3])


class TestAll:
    def test_all(self):
        eq_(QuerySet(X).all().query, Q())


class TestFilter:
    def filter(self, *args, **kwargs):
        return QuerySet(X).filter(*args, **kwargs).query

    def test_filter(self):
        eq_(self.filter(), Q())

    def test_with_args(self):
        eq_(self.filter(Q(a=1)), Q(a=1))
        eq_(self.filter(Q(a=1), Q(b=2)), Q(a=1, b=2))

    def test_with_kwargs(self):
        eq_(self.filter(a=1), Q(a=1))
        eq_(self.filter(a=1, b=2), Q(a=1, b=2))

    def test_with_args_and_kwargs(self):
        eq_(self.filter(Q(a=1), b=2), Q(a=1, b=2))
        eq_(self.filter(Q(a=1), Q(b=2), c=3), Q(a=1, b=2, c=3))
        eq_(self.filter(Q(a=1), b=2, c=3), Q(a=1, b=2, c=3))
        eq_(self.filter(Q(a=1), Q(b=2), c=3, d=4), Q(a=1, b=2, c=3, d=4))


class TestExclude:
    def exclude(self, *args, **kwargs):
        return QuerySet(X).exclude(*args, **kwargs).query

    def test_exclude(self):
        eq_(self.exclude(), ~Q())

    def test_with_args(self):
        eq_(self.exclude(Q(a=1)), ~Q(a=1))
        eq_(self.exclude(Q(a=1), Q(b=2)), ~Q(a=1, b=2))

    def test_with_kwargs(self):
        eq_(self.exclude(a=1), ~Q(a=1))
        eq_(self.exclude(a=1, b=2), ~Q(a=1, b=2))

    def test_with_args_and_kwargs(self):
        eq_(self.exclude(Q(a=1), b=2), ~Q(a=1, b=2))
        eq_(self.exclude(Q(a=1), Q(b=2), c=3), ~Q(a=1, b=2, c=3))
        eq_(self.exclude(Q(a=1), b=2, c=3), ~Q(a=1, b=2, c=3))
        eq_(self.exclude(Q(a=1), Q(b=2), c=3, d=4), ~Q(a=1, b=2, c=3, d=4))


class TestOrderBy:
    def order_by(self, *args):
        return QuerySet(X).order_by(*args).query

    def test_order_by(self):
        eq_(self.order_by(), Q().order_by())
        eq_(self.order_by('a'), Q().order_by('a'))
        eq_(self.order_by('a', '-b'), Q().order_by('a', '-b'))


class TestChaining:
    def filter_exclude(self):
        eq_(QuerySet(X).filter(a=1).exclude(b=2).query, Q(a=1) & ~Q(b=2))

    def filter_order_by(self):
        eq_(QuerySet(X).filter(a=1).order_by('b').query, Q(a=1).order_by('b'))

    def filter_slice(self):
        eq_(QuerySet(X).filter(a=1)[:3].query, Q(a=1)[:3])

    def exclude_filter(self):
        eq_(QuerySet(X).exclude(a=1).filter(b=2).query, ~Q(a=1) & Q(b=2))

    def exclude_order_by(self):
        eq_(QuerySet(X).exclude(a=1).order_by('b').query, ~Q(a=1).order_by('b'))

    def exclude_slice(self):
        eq_(QuerySet(X).exclude(a=1)[:3].query, ~Q(a=1)[:3])

    def order_by_filter(self):
        eq_(QuerySet(X).order_by('a').filter(b=2).query,
            Q().order_by('a') & Q(b=2))

    def order_by_exclude(self):
        eq_(QuerySet(X).order_by('a').exclude(b=2).query,
            Q().order_by('a') & ~Q(b=2))

    def order_by_slice(self):
        eq_(QuerySet(X).order_by('a')[:3].query, Q().order_by('a')[:3])

    def slice_filter(self):
        eq_(QuerySet(X)[:3].filter(a=1).query, Q()[:3] & Q(a=1))

    def slice_exclude(self):
        eq_(QuerySet(X)[:3].exclude(a=1).query, Q()[:3] & ~Q(a=1))

    def slice_order_by(self):
        eq_(QuerySet(X)[:3].order_by('a').query, Q()[:3].order_by('a'))


class TestExecute:
    @patch('git_orm.models.queryset.ObjCache')
    def test_execute(self, MockCache):
        obj_cache = Mock(pks=[1, 2, 3, 4])
        MockCache.return_value = obj_cache

        qs = QuerySet(X)
        qs.query = MagicMock()
        qs.query.__and__.return_value = qs.query
        qs.query.execute.return_value = [1, 2, 3]

        eq_(qs._execute(a=1, b=2), ([1, 2, 3], obj_cache))
        qs.query.__and__.assert_called_once_with(Q(a=1, b=2))
        qs.query.execute.assert_called_once_with(obj_cache, obj_cache.pks)

    def test_zero(self):
        qs = QuerySet(X)
        qs._execute = lambda: (iter([]), {})
        assert_raises(X.DoesNotExist, qs.get)
        ok_(not qs.exists())
        eq_(qs.count(), 0)
        eq_(list(qs), [])

    def test_one(self):
        x = X()
        qs = QuerySet(X)
        qs._execute = lambda: (iter([0]), {0: x})
        eq_(qs.get(), x)
        ok_(qs.exists())
        eq_(qs.count(), 1)
        eq_(list(qs), [x])

    def test_two(self):
        x1 = X()
        x2 = X()
        qs = QuerySet(X)
        qs._execute = lambda: (iter([0, 1]), {0: x1, 1: x2})
        assert_raises(X.MultipleObjectsReturned, qs.get)
        ok_(qs.exists())
        eq_(qs.count(), 2)
        eq_(list(qs), [x1, x2])
