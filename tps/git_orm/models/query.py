import re
from itertools import islice


class Query:
    def __or__(self, other):
        for a, b in ((self, other), (other, self)):
            if a == Q():
                return a
            elif a == ~Q():
                return b
            elif isinstance(a, Inversion) and a.subquery == b:
                return Q()
            elif isinstance(a, Union):
                if isinstance(b, Union):
                    return Union(*(a.subqueries | b.subqueries))
                else:
                    return Union(b, *a.subqueries)
        return Union(self, other)

    def __and__(self, other):
        for a, b in ((self, other), (other, self)):
            if a == Q():
                return b
            elif a == ~Q():
                return a
            elif isinstance(a, Inversion) and a.subquery == b:
                return ~Q()
            elif isinstance(a, Intersection):
                if isinstance(b, Intersection):
                    return Intersection(*(a.subqueries | b.subqueries))
                else:
                    return Intersection(b, *a.subqueries)
        if isinstance(self, Q) and isinstance(other, Q):
            q = Q()
            q.conditions = self.conditions | other.conditions
            return q
        return Intersection(self, other)

    def __invert__(self):
        if isinstance(self, Inversion):
            return self.subquery
        return Inversion(self)

    def __getitem__(self, key):
        # XXX: implement optimizations for slicing?
        if isinstance(key, slice):
            return Slice(self, key)
        raise TypeError('index must be a slice')

    def __ne__(self, other):
        # __eq__ has to be implemented for every subclass separately
        return not self == other

    def order_by(self, *order_by):
        # XXX: does it make sense to call order_by without arguments?
        # XXX: implement optimizations for order_by?
        return Ordered(self, *order_by)

    def execute(self, obj_cache, pks):
        raise NotImplementedError


class Q(Query):
    OPERATORS = {
        'exact': lambda x, y: x == y,
        'iexact': lambda x, y: x.lower() == y.lower(),
        'contains': lambda x, y: y in x,
        'icontains': lambda x, y: y.lower() in x.lower(),
        'in': lambda x, y: x in y,
        'gt': lambda x, y: x > y,
        'gte': lambda x, y: x >= y,
        'lt': lambda x, y: x < y,
        'lte': lambda x, y: x > y,
        'startswith': lambda x, y: x.startswith(y),
        'istartswith': lambda x, y: x.lower().startswith(y.lower()),
        'endswith': lambda x, y: x.endswith(y),
        'iendswith': lambda x, y: x.lower().endswith(y.lower()),
        'range': lambda x, y: y[0] <= x <= y[1],
        'isnull': lambda x, y: x is None if y else x is not None,

        # XXX: compiling the regex on every invocation is slow
        'regex': lambda x, y: re.search(y, x),
        'iregex': lambda x, y: re.search(y, x, re.IGNORECASE),
    }

    def __init__(self, **kwargs):
        conditions = set()
        for key, value in kwargs.items():
            field, sep, op = key.partition('__')
            if not sep:
                op = 'exact'
            conditions.add((field, op, value))
        self.conditions = frozenset(conditions)

    def __repr__(self):
        conditions = []
        for field, op, value in self.conditions:
            conditions.append('{}__{}={!r}'.format(field, op, value))
        return 'Q({})'.format(', '.join(conditions))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.conditions == other.conditions)

    def __hash__(self):
        return hash(self.conditions)

    def match(self, obj_cache, pk):
        for field, op, value in self.conditions:
            op = self.OPERATORS[op]
            if field in obj_cache.pk_names and not op(pk, value):
                return False
            else:
                obj = obj_cache[pk]
                if not op(getattr(obj, field), value):
                    return False
        return True

    def execute(self, obj_cache, pks):
        return (pk for pk in pks if self.match(obj_cache, pk))


class Inversion(Query):
    def __init__(self, subquery):
        self.subquery = subquery

    def __repr__(self):
        return '~{!r}'.format(self.subquery)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.subquery == other.subquery)

    def __hash__(self):
        return hash(self.subquery)

    def execute(self, obj_cache, pks):
        matched = set(self.subquery.execute(obj_cache, pks))
        return (pk for pk in pks if not pk in matched)


class Intersection(Query):
    def __init__(self, *subqueries):
        self.subqueries = frozenset(subqueries)

    def __repr__(self):
        bits = (repr(query) for query in self.subqueries)
        return '({})'.format(' & '.join(bits))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.subqueries == other.subqueries)

    def __hash__(self):
        return hash(self.subqueries)

    def execute(self, obj_cache, pks):
        for subquery in self.subqueries:
            pks = subquery.execute(obj_cache, list(pks))
        return pks


class Union(Query):
    def __init__(self, *subqueries):
        self.subqueries = frozenset(subqueries)

    def __repr__(self):
        bits = (repr(query) for query in self.subqueries)
        return '({})'.format(' | '.join(bits))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.subqueries == other.subqueries)

    def __hash__(self):
        return hash(self.subqueries)

    def execute(self, obj_cache, pks):
        pks = set(pks)
        for subquery in self.subqueries:
            for pk in subquery.execute(obj_cache, list(pks)):
                pks.discard(pk)
                yield pk


class Slice(Query):
    def __init__(self, subquery, slice_):
        self.subquery = subquery
        self.slice = (slice_.start, slice_.stop, slice_.step)

    def __repr__(self):
        bits = list(self.slice[:2])
        if not self.slice[2] is None:
            bits.append(self.slice[2])
        bits = ['' if bit is None else str(bit) for bit in bits]
        return '{!r}[{}]'.format(self.subquery, ':'.join(bits))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.subquery == other.subquery and self.slice == other.slice)

    def __hash__(self):
        return hash((self.subquery, self.slice))

    def execute(self, obj_cache, pks):
        return islice(self.subquery.execute(obj_cache, pks), *self.slice)


class SortableNix:
    def __init__(self, reverse):
        self.reverse = reverse

    def __lt__(self, other):
        if isinstance(other, SortableNix):
            return self.reverse
        return True

    def __gt__(self, other):
        if isinstance(other, SortableNix):
            return not self.reverse
        return False


class Ordered(Query):
    def __init__(self, subquery, *order_by):
        self.subquery = subquery
        self.order_by = order_by

    def __repr__(self):
        bits = (repr(bit) for bit in self.order_by)
        return '{!r}.order_by({})'.format(self.subquery, ', '.join(bits))

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.subquery == other.subquery and
            self.order_by == other.order_by)

    def __hash__(self):
        return hash((self.subquery, self.order_by))

    def execute(self, obj_cache, pks):
        pks = list(self.subquery.execute(obj_cache, pks))
        for field in reversed(self.order_by):
            reverse = False
            if field.startswith('-'):
                field = field[1:]
                reverse = True
            if field in obj_cache.pk_names:
                pks.sort(reverse=reverse)
                continue

            def _key(pk):
                val = getattr(obj_cache[pk], field)
                if val is None:
                    val = SortableNix(reverse)
                return val

            pks.sort(key=_key, reverse=reverse)
        return iter(pks)
