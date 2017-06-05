import time
from datetime import datetime, timedelta, timezone

from git_orm import transaction

from django.db.models.fields import Field as DjangoField
from django import forms

__all__ = [
    'TextField', 'ForeignKey', 'DateTimeField', 'CreatedAtField',
    'UpdatedAtField'
]




class Field(DjangoField):
    def __init__(
            self, auto_created=False, null=False, primary_key=False, choices=None,
            default=None, name=None, **kwargs):
        super(Field, self).__init__(**kwargs)
        self.auto_created = auto_created
        self.null = null
        self.primary_key = primary_key
        self.choices = choices
        self.default = default
        self.name = name


    def contribute_to_class(self, cls, name):
        if not self.name:
            self.name = name
        self.set_attributes_from_name(name)
        self.attname = self.get_attname()
        self.model = cls
        cls._meta.add_field(self)

    def get_attname(self):
        return self.name

    def get_default(self):
        if callable(self.default):
            return self.default()
        return self.default

    def validate(self, value):
        if value is None:
            if not self.null:
                raise ValueError('{} must not be None'.format(self.name))
        elif not self.choices is None and not value in self.choices:
            raise ValueError(
                '{} must be in {}'.format(self.name, self.choices))

    def dumps(self, value):
        return value

    def loads(self, value):
        return value

    def __lt__(self, other):
        return self.name < other.name


class TextField(Field):
    def validate(self, value):
        super().validate(value)
        if not value is None and not isinstance(value, str):
            raise ValueError('{} must be a string'.format(self.name))


class ForeignKeyDescriptor:
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if not hasattr(self, '_cache'):
            pk = getattr(instance, self.field.attname)
            if pk is None:
                obj = None
            else:
                obj = self.field.target.objects.get(pk=pk)
            self._cache = obj
        return self._cache

    def __set__(self, instance, value):
        if isinstance(value, self.field.target):
            pk = value.pk
            self._cache = value
        else:
            pk = value
            try:
                del self._cache
            except AttributeError:
                pass
        setattr(instance, self.field.attname, pk)


class ForeignKey(Field):
    def __init__(self, target, **kwargs):
        super(ForeignKey, self).__init__(**kwargs)
        self.target = target

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, ForeignKeyDescriptor(self))

    def get_attname(self):
        return '_'.join([self.name, self.target._meta.pk.attname])

    def validate(self, value):
        if not value is None and not self.target.objects.exists(pk=value):
            target_name = self.target.__name__
            raise ValueError(
                '{} with pk={!r} does not exist'.format(target_name, value))

    def dumps(self, value):
        if not value is None:
            pk_field = self.target._meta.pk
            return pk_field.dumps(value)
        return None

    def loads(self, value):
        if not value is None:
            pk_field = self.target._meta.pk
            return pk_field.loads(value)
        return None


class DateTimeField(Field):
    FORMAT = '%Y-%m-%d %H:%M:%S %z'

    def validate(self, value):
        super().validate(value)
        if not value is None and not isinstance(value, datetime):
            raise ValueError('{} must be a datetime object'.format(self.name))

    def dumps(self, value):
        if not value is None:
            if not value.tzinfo:
                # Take a deep breath...
                zone = time.timezone
                if time.daylight and time.localtime().tm_isdst == 1:
                    zone = time.altzone
                tz = timezone(timedelta(seconds=-zone))
                value = value.replace(tzinfo=tz)
            return value.strftime(self.FORMAT)
        return None

    def loads(self, value):
        if not value is None:
            return datetime.strptime(value, self.FORMAT)
        return None


class CreatedAtField(Field):
    def get_attname(self):
        return None

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, CreatedAtDescriptor())


class CreatedAtDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        with transaction.wrap() as trans:
            if instance.pk:
                return trans.stat(instance.path).created_at
            return None


class UpdatedAtField(Field):
    def get_attname(self):
        return None

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, UpdatedAtDescriptor())


class UpdatedAtDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        with transaction.wrap() as trans:
            if instance.pk:
                return trans.stat(instance.path).updated_at
            return None
