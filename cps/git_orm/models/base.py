from collections import OrderedDict

from git_orm import serializer, transaction
from git_orm.models.options import Options
from git_orm.models.fields import ForeignKey
from git_orm.models.queryset import QuerySet


class DoesNotExist(Exception):
    pass


class MultipleObjectsReturned(Exception):
    pass


class InvalidObject(Exception):
    pass


MODEL_EXCEPTIONS = (DoesNotExist, MultipleObjectsReturned, InvalidObject)


class ModelBase(type):
    @classmethod
    def __prepare__(cls, name, bases):
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if parents:
            return OrderedDict()
        return super().__prepare__(name, bases)

    def __new__(cls, cls_name, bases, attrs):
        super_new = super().__new__
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            return super_new(cls, cls_name, bases, attrs)

        module = attrs.pop('__module__')
        new_class = super_new(cls, cls_name, bases, {'__module__': module})

        opts = Options(attrs.pop('Meta', None))
        new_class.add_to_class('_meta', opts)

        objects = attrs.pop('objects', None)
        if objects is None:
            objects = QuerySet(new_class)
        new_class.add_to_class('objects', objects)

        for exc_class in MODEL_EXCEPTIONS:
            name = exc_class.__name__
            exc_class = type(name, (exc_class,), {'__module__': module})
            new_class.add_to_class(name, exc_class)

        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        opts._prepare()
        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


class Model(metaclass=ModelBase):
    def __init__(self, **kwargs):
        for field in self._meta.writable_fields:
            attname = field.attname
            if isinstance(field, ForeignKey):
                attname = field.name
            try:
                val = kwargs.pop(attname)
            except KeyError:
                val = field.get_default()
            setattr(self, attname, val)
        if kwargs:
            for prop in list(kwargs.keys()):
                try:
                    if isinstance(getattr(self.__class__, prop), property):
                        setattr(self, prop, kwargs.pop(prop))
                except AttributeError:
                    pass
            if kwargs:
                name = list(kwargs.keys())[0]
                raise TypeError('invalid keyword argument \'{}\''.format(name))

    def __repr__(self):
        try:
            fn = getattr(self, 'get_{}_display'.format(self._meta.pk.name))
        except AttributeError:
            pk_display = self.pk
        else:
            pk_display = fn()
        return '<{}: {}>'.format(self.__class__.__name__, pk_display)

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.pk)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.pk == other.pk

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.pk)

    def _get_pk_val(self):
        return getattr(self, self._meta.pk.attname)

    def _set_pk_val(self, value):
        return setattr(self, self._meta.pk.attname, value)

    pk = property(_get_pk_val, _set_pk_val)

    def dumps(self, include_hidden=False, include_pk=True):
        data = OrderedDict()
        for field in self._meta.writable_fields:
            if field.name == self._meta.pk.name and not include_pk:
                continue
            if field.hidden and not include_hidden:
                continue
            value = getattr(self, field.attname)
            data[field.name] = field.dumps(value)
        return serializer.dumps(data)

    def loads(self, data):
        try:
            if not hasattr(data, 'items'):
                data = serializer.loads(data)
            for field_name, value in data.items():
                field = self._meta.get_field(field_name)
                setattr(self, field.attname, field.loads(value))
        except (ValueError, KeyError) as e:
            raise self.InvalidObject(e)

    @property
    def path(self):
        pk = self.pk
        if pk is None:
            raise ValueError('pk must not be None')
        pk = self._meta.pk.dumps(self.pk)
        return [self._meta.storage_name, pk]

    @transaction.wrap()
    def save(self):
        for field in self._meta.writable_fields:
            try:
                field.validate(getattr(self, field.attname))
            except ValueError as e:
                raise self.InvalidObject(e)
        trans = transaction.current()
        serialized = self.dumps(include_hidden=True, include_pk=False)
        trans.set_blob(self.path, serialized.encode('utf-8'))
        # TODO: create informative commit message
        trans.add_message('Edit {}'.format(self))

    @transaction.wrap()
    def delete(self):
        raise NotImplementedError()

    @classmethod
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj
