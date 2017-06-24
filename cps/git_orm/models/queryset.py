import copy
import logging

from functools import reduce
from git_orm import transaction as git_transaction, GitError
from git_orm.models.query import Q
from git_orm.transaction import Transaction

logger = logging.getLogger(__name__)


class ObjCache(object):
    def __init__(self, model, transaction):
        self.model = model
        self.transaction = transaction
        self.cache = {}
        self.pks = set(map(model._meta.pk.to_python, model._get_existing_primary_keys(transaction)))
        self.pk_names = ('pk', model._meta.pk.attname)

    def __getitem__(self, pk):
        if not pk in self.cache:
            self.cache[pk] = self.model._get_instance(self.transaction, pk)
        return self.cache[pk]


class QuerySet(object):
    REPR_MAXLEN = 10

    def __init__(self, model, query=None, transaction=None):
        self.model = model
        if query is None:
            query = Q()
        self.query = query
        self.transaction = transaction

    def get_transaction(self):
        if self.transaction is not None:
            return self.transaction
        return git_transaction.current()


    def __repr__(self):
        evaluated = list(self[:self.REPR_MAXLEN+1])
        if len(evaluated) > self.REPR_MAXLEN:
            bits = (repr(bit) for bit in evaluated[:self.REPR_MAXLEN-1])
            return '[{}, ...]'.format(', '.join(bits))
        return repr(evaluated)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and self.model == other.model and
            self.query == other.query)

    def __ne__(self, other):
        return not self == other

    def __or__(self, other):
        return QuerySet(self.model, self.query | other.query, self.transaction)

    def __and__(self, other):
        return QuerySet(self.model, self.query & other.query, self.transaction)

    def __invert__(self):
        return QuerySet(self.model, ~self.query, self.transaction)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return QuerySet(self.model, self.query[key], self.transaction)
        elif isinstance(key, int):
            try:
                stop = key + 1
                if stop == 0:
                    stop = None
                return QuerySet(self.model, self.query[key:stop], self.transaction).get()
            except self.model.DoesNotExist:
                raise IndexError('index out of range')
        else:
            raise TypeError('indices must be integers')

    def with_transaction(self, transaction):
        if transaction is None:
            raise ValueError("transaction cannot be None")
        if not isinstance(transaction, Transaction):
            raise ValueError("invalid transaction")
        return QuerySet(self.model, self.query, transaction)

    def __iter__(self):
        pks, obj_cache = self._execute()
        return iter([obj_cache[pk] for pk in pks])

    def _execute(self, *args, **kwargs):
        query = self.query & self._filter(*args, **kwargs)
        obj_cache = ObjCache(self.model, self.get_transaction())
        return query.execute(obj_cache, obj_cache.pks), obj_cache

    def _filter(self, *args, **kwargs):
        return reduce(lambda x, y: x & y, args, Q(**kwargs))

    def all(self):
        return self

    def filter(self, *args, **kwargs):
        query = self.query & self._filter(*args, **kwargs)
        return QuerySet(self.model, query, self.transaction)

    def exclude(self, *args, **kwargs):
        query = self.query & ~self._filter(*args, **kwargs)
        return QuerySet(self.model, query, self.transaction)

    def get(self, *args, **kwargs):
        pks, obj_cache = self._execute(*args, **kwargs)
        try:
            pk = next(pks)
        except StopIteration:
            raise self.model.DoesNotExist('object does not exist')
        try:
            next(pks)
        except StopIteration:
            pass
        else:
            raise self.model.MultipleObjectsReturned(
                'multiple objects returned')
        return obj_cache[pk]

    def exists(self, *args, **kwargs):
        pks, _ = self._execute(*args, **kwargs)
        try:
            next(pks)
        except StopIteration:
            return False
        return True

    def count(self, *args, **kwargs):
        pks, _ = self._execute(*args, **kwargs)
        return sum(1 for _ in pks)

    def order_by(self, *order_by):
        return QuerySet(self.model, self.query.order_by(*order_by), self.transaction)

    def create(self, *args, **kwargs):
        return self.model.create(*args, transaction=self.transaction, **kwargs)

    def _copy_to_model(self, model):
        assert issubclass(model, self.model)
        qst = copy.copy(self)
        qst.model = model
        return qst

    def get_or_create(self, defaults=None, **kwargs):
        if defaults:
            parameters = defaults.copy()
        else:
            parameters = {}
        parameters.update(kwargs)
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            return self.create(**parameters), True
