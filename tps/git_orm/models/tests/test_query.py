from itertools import combinations
from random import choice, shuffle

from nose.tools import *
from nose.plugins.skip import SkipTest
from mock import Mock

from git_orm.models.query import (
    Query, Q, Inversion, Intersection, Union, Slice, Ordered)


def generate_conditions():
    operators = Q.OPERATORS.keys()
    for i in range(3):
        for ops in combinations(operators, i):
            d = {}
            for op in ops:
                field_name = choice(('foo', 'bar', 'baz'))
                lookup = '{}__{}'.format(field_name, op) if op else field_name
                d[lookup] = 42
            yield d


class TestQ:
    def test_equality(self):
        for conditions in generate_conditions():
            eq_(Q(**conditions), Q(**conditions))

    def test_inequality(self):
        cond = iter(generate_conditions())
        for conditions1, conditions2 in zip(cond, cond):
            assert_not_equal(Q(**conditions1), Q(**conditions2))

    def test_repr(self):
        for conditions in generate_conditions():
            q = Q(**conditions)
            eq_(q, eval(repr(q)))

    def test_match(self):
        raise SkipTest()


class TestInversion:
    def test_equality(self):
        for conditions in generate_conditions():
            q = Q(**conditions)
            eq_(Inversion(q), Inversion(q))

    def test_inequality(self):
        cond = iter(generate_conditions())
        for conditions1, conditions2 in zip(cond, cond):
            assert_not_equal(~Q(**conditions1), ~Q(**conditions2))

    def test_repr(self):
        for conditions in generate_conditions():
            q = ~Q(**conditions)
            eq_(q, eval(repr(q)))


class TestIntersection:
    def test_equality(self):
        cond = iter(generate_conditions())
        for conditions1, conditions2 in zip(cond, cond):
            qs = (Q(**conditions1), Q(**conditions2))
            eq_(Intersection(*qs), Intersection(*qs))

    def test_inequality(self):
        cond = iter(generate_conditions())
        cond = iter(zip(cond, cond))
        for conditions1, conditions2 in zip(cond, cond):
            qs1 = (Q(**conditions1[0]), Q(**conditions1[1]))
            qs2 = (Q(**conditions2[0]), Q(**conditions2[1]))
            assert_not_equal(Intersection(*qs1), Intersection(*qs2))

    def test_repr(self):
        cond = iter(generate_conditions())
        for conditions1, conditions2 in zip(cond, cond):
            q = Q(**conditions1) | Q(**conditions2)
            eq_(q, eval(repr(q)))


class TestUnion:
    def test_equality(self):
        cond = iter(generate_conditions())
        for conditions1, conditions2 in zip(cond, cond):
            qs = (Q(**conditions1), Q(**conditions2))
            eq_(Union(*qs), Union(*qs))

    def test_inequality(self):
        cond = iter(generate_conditions())
        cond = iter(zip(cond, cond))
        for conditions1, conditions2 in zip(cond, cond):
            qs1 = (Q(**conditions1[0]), Q(**conditions1[1]))
            qs2 = (Q(**conditions2[0]), Q(**conditions2[1]))
            assert_not_equal(Union(*qs1), Union(*qs2))

    def test_repr(self):
        cond = iter(generate_conditions())
        for conditions1, conditions2 in zip(cond, cond):
            q = Q(**conditions1) & Q(**conditions2)
            eq_(q, eval(repr(q)))


class TestSlice:
    def test_equality(self):
        for s in ((None,), (0,), (0, 3), (0, 3, 2)):
            eq_(Slice(Q(), slice(*s)), Slice(Q(), slice(*s)))

    def test_inequality(self):
        args = iter(((None,), (0,), (0, 3), (0, 3, 2)))
        for s1, s2 in zip(args, args):
            assert_not_equal(Slice(Q(), slice(*s1)), Slice(Q(), slice(*s2)))

    def test_repr(self):
        for s in ((None,), (0,), (0, 3), (0, 3, 2)):
            q = Q()[slice(*s)]
            eq_(q, eval(repr(q)))


class TestOrdered:
    def test_equality(self):
        for fields in ((), ('foo',), ('foo', '-bar'), ('foo', '-bar', 'baz')):
            eq_(Ordered(Q(), *fields), Ordered(Q(), *fields))

    def test_inequality(self):
        args = iter(((), ('foo',), ('foo', '-bar'), ('foo', '-bar', 'baz')))
        for fields1, fields2 in zip(args, args):
            assert_not_equal(Ordered(Q(), *fields1), Ordered(Q(), *fields2))

    def test_repr(self):
        for fields in ((), ('foo',), ('foo', '-bar'), ('foo', '-bar', 'baz')):
            q = Q().order_by(*fields)
            eq_(q, eval(repr(q)))


class TestExecute:
    def setup(self):
        self.pks = list(range(10))
        self.obj_cache = Mock()
        self.mock_qs = []

    def teardown(self):
        for q, expected_pks in self.mock_qs:
            q.execute.assert_called_once_with(self.obj_cache, expected_pks)

    def assert_execute(self, q, expected_result):
        eq_(list(q.execute(self.obj_cache, self.pks)), expected_result)

    def mock_q(self, expected_pks, rval):
        q = Mock(execute=Mock(return_value=rval))
        self.mock_qs.append((q, expected_pks))
        return q

    def test_q(self):
        matching = [2, 3, 5, 7]
        q = Q()
        q.match = lambda obj_cache, pk: pk in matching
        self.assert_execute(q, matching)

    def test_inversion(self):
        subquery = self.mock_q(self.pks, [0, 4, 6, 7, 8, 9])
        self.assert_execute(Inversion(subquery), [1, 2, 3, 5])

    def test_intersection(self):
        subqueries = (
            self.mock_q(self.pks, [0, 1, 2, 3, 4]),
            self.mock_q([0, 1, 2, 3, 4], [0, 2, 4]),
            self.mock_q([0, 2, 4], [4]),
        )
        q = Intersection()
        q.subqueries = subqueries
        self.assert_execute(q, [4])

    def test_union(self):
        subqueries = (
            self.mock_q(self.pks, [4, 7, 8]),
            self.mock_q([0, 1, 2, 3, 5, 6, 9], [1, 2, 3]),
            self.mock_q([0, 5, 6, 9], [5]),
        )
        q = Union()
        q.subqueries = subqueries
        self.assert_execute(q, [4, 7, 8, 1, 2, 3, 5])

    def test_slice(self):
        subquery = self.mock_q(self.pks, [0, 1, 2, 3, 4])
        self.assert_execute(Slice(subquery, slice(1, 4)), [1, 2, 3])

    def test_ordered(self):
        shuffled = self.pks[:]
        shuffle(shuffled)
        subquery = self.mock_q(self.pks, shuffled)
        self.obj_cache.pk_names = ('pk', 'id')
        self.assert_execute(Ordered(subquery, 'pk'), self.pks)


class TestOperators:
    def test_union(self):
        a, b = Query(), Query()
        q = a | b
        assert_is_instance(q, Union)
        assert_set_equal(q.subqueries, set((a, b)))

    def test_intersection(self):
        a, b = Query(), Query()
        q = a & b
        assert_is_instance(q, Intersection)
        assert_set_equal(q.subqueries, set((a, b)))

    def test_inversion(self):
        q = Query()
        assert_is_instance(~q, Inversion)
        eq_((~q).subquery, q)


class TestUnionOptimizations:
    def check_both(self, a, b, result):
        eq_(a | b, result)
        eq_(b | a, result)

    def test_with_everything(self):
        self.check_both(Q(), Query(), Q())

    def test_with_nothing(self):
        q = Query()
        self.check_both(~Q(), q, q)

    def test_query_with_its_inversion(self):
        q = Query()
        self.check_both(q, ~q, Q())

    def test_query_with_union(self):
        a, b, c = Query(), Query(), Query()
        self.check_both(a | b, c, Union(a, b, c))

    def test_union_with_union(self):
        a, b, c, d = Query(), Query(), Query(), Query()
        self.check_both(a | b, c | d, Union(a, b, c, d))


class TestIntersectionOptimizations:
    def check_both(self, a, b, result):
        eq_(a & b, result)
        eq_(b & a, result)

    def test_intersection_everything(self):
        q = Query()
        self.check_both(Q(), q, q)

    def test_intersection_nothing(self):
        self.check_both(~Q(), Query(), ~Q())

    def test_intersection_query_with_its_inversion(self):
        q = Query()
        self.check_both(q, ~q, ~Q())

    def test_query_with_intersection(self):
        a, b, c = Query(), Query(), Query()
        self.check_both(a & b, c, Intersection(a, b, c))

    def test_intersection_with_intersection(self):
        a, b, c, d = Query(), Query(), Query(), Query()
        self.check_both(a & b, c & d, Intersection(a, b, c, d))

    def test_q_intersection(self):
        q = Q(foo=42) & Q(bar=42)
        eq_(q, Q(foo=42, bar=42))
        assert_is_instance(q, Q)


class TestInversionOptimizations:
    def test_inversion_inversion(self):
        q = Q(foo=42)
        assert_is(~~q, q)
