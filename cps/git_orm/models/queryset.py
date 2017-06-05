from functools import reduce

from git_orm import transaction, GitError
from git_orm.models.query import Q


class ObjCache:
    def __init__(self, model):
        self.model = model
        self.cache = {}
        pks = transaction.current().list_blobs([model._meta.storage_name])
        self.pks = set(map(model._meta.pk.loads, pks))
        self.pk_names = ('pk', model._meta.pk.attname)

    def __getitem__(self, pk):
        if not pk in self.cache:
            obj = self.model(pk=pk)
            try:
                trans = transaction.current()
                content = trans.get_blob(obj.path).decode('utf-8')
            except GitError:
                raise self.model.DoesNotExist(
                    'object with pk {} does not exist'.format(pk))
            obj.loads(content)
            self.cache[pk] = obj
        return self.cache[pk]


class QuerySet:
    REPR_MAXLEN = 10

    def __init__(self, model, query=None):
        self.model = model
        if query is None:
            query = Q()
        self.query = query

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
        return QuerySet(self.model, self.query | other.query)

    def __and__(self, other):
        return QuerySet(self.model, self.query & other.query)

    def __invert__(self):
        return QuerySet(self.model, ~self.query)

    @transaction.wrap()
    def __getitem__(self, key):
        if isinstance(key, slice):
            return QuerySet(self.model, self.query[key])
        elif isinstance(key, int):
            try:
                stop = key + 1
                if stop == 0:
                    stop = None
                return QuerySet(self.model, self.query[key:stop]).get()
            except self.model.DoesNotExist:
                raise IndexError('index out of range')
        else:
            raise TypeError('indices must be integers')

    @transaction.wrap()
    def __iter__(self):
        pks, obj_cache = self._execute()
        return iter([obj_cache[pk] for pk in pks])

    def _execute(self, *args, **kwargs):
        query = self.query & self._filter(*args, **kwargs)
        obj_cache = ObjCache(self.model)
        return query.execute(obj_cache, obj_cache.pks), obj_cache

    def _filter(self, *args, **kwargs):
        return reduce(lambda x, y: x & y, args, Q(**kwargs))

    def all(self):
        return self

    def filter(self, *args, **kwargs):
        query = self.query & self._filter(*args, **kwargs)
        return QuerySet(self.model, query)

    def exclude(self, *args, **kwargs):
        query = self.query & ~self._filter(*args, **kwargs)
        return QuerySet(self.model, query)

    @transaction.wrap()
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

    @transaction.wrap()
    def exists(self, *args, **kwargs):
        pks, _ = self._execute(*args, **kwargs)
        try:
            next(pks)
        except StopIteration:
            return False
        return True

    @transaction.wrap()
    def count(self, *args, **kwargs):
        pks, _ = self._execute(*args, **kwargs)
        return sum(1 for _ in pks)

    def order_by(self, *order_by):
        return QuerySet(self.model, self.query.order_by(*order_by))

    def create(self, *args, **kwargs):
        return self.model.create(*args, **kwargs)
