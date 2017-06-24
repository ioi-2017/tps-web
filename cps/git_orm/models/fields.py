import time
from datetime import datetime, timedelta, timezone

from django.db.models.fields.related import lazy_related_operation

from git_orm import transaction

from django.db.models.fields import Field as DjangoField

__all__ = [
    'TextField', 'GitToGitForeignKey', 'DateTimeField', 'CreatedAtField',
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

    def contribute_to_class(self, cls, name, virtual=False):
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

    def validate(self, value, model_instance):
        if value is None:
            if not self.null:
                raise ValueError('{} must not be None'.format(self.name))
        elif not self.choices is None and not value in self.choices:
            raise ValueError(
                '{} must be in {}'.format(self.name, self.choices))

    def get_prep_value(self, value):
        return value

    def to_python(self, value):
        return value

    def __lt__(self, other):
        return self.name < other.name


class TextField(Field):
    def validate(self, value, *args, **kwargs):
        super().validate(value, *args, **kwargs)
        if not value is None and not isinstance(value, str):
            raise ValueError('{} must be a string'.format(self.name))


class GitToGitForeignKeyDescriptor(object):
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
                obj = self.field.target.objects.with_transaction(instance._transaction).get(pk=pk)
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


class ReverseForeignKeyDescriptor(object):

    def __init__(self, target):
        self.target_field = target

    def __get__(self, instance, instance_type=None):
        """
        Get the related objects through the reverse relation.

        With the example above, when getting ``parent.children``:

        - ``self`` is the descriptor managing the ``children`` attribute
        - ``instance`` is the ``parent`` instance
        - ``instance_type`` in the ``Parent`` class (we don't need it)
        """
        if instance is None:
            return self

        return self.target_field.model.objects.with_transaction(instance._transaction).filter(**{
            self.target_field.attname: instance.pk})


class GitToGitForeignKey(Field):

    forward_descriptor = GitToGitForeignKeyDescriptor
    reverse_descriptor = ReverseForeignKeyDescriptor

    def __init__(self, target, related_name=None, **kwargs):
        super(GitToGitForeignKey, self).__init__(**kwargs)
        self.target = target
        self.related_name = related_name

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, self.forward_descriptor(self))

        def resolve_related_class(model, related, field):
            field.target = related
            field.do_related_class(related, model)

        lazy_related_operation(resolve_related_class, cls, self.target, field=self)

    def get_attname(self):
        return '%s_id' % self.name

    def validate(self, value, *args, **kwargs):
        if not value is None and not self.target.objects.exists(pk=value):
            target_name = self.target.__name__
            raise ValueError(
                '{} with pk={!r} does not exist'.format(target_name, value))

    def set_attributes_from_rel(self):
        self.name = (
            self.name or
            (self.target._meta.model_name + '_' + self.target._meta.pk.name)
        )
        if self.verbose_name is None:
            self.verbose_name = self.target._meta.verbose_name

    def get_accessor_name(self, model=None):
        # This method encapsulates the logic that decides what name to give an
        # accessor descriptor that retrieves related many-to-one or
        # many-to-many objects. It uses the lower-cased object_name + "_set",
        # but this can be overridden with the "related_name" option.
        # Due to backwards compatibility ModelForms need to be able to provide
        # an alternate model. See BaseInlineFormSet.get_default_prefix().
        opts = model._meta if model else self.model._meta
        if self.related_name:
            return self.related_name
        if opts.default_related_name:
            return opts.default_related_name % {
                'model_name': opts.model_name.lower(),
                'app_label': opts.app_label.lower(),
            }
        return opts.model_name + '_set'

    def do_related_class(self, other, cls):
        self.set_attributes_from_rel()
        if self.get_accessor_name() != '+':
            setattr(other, self.get_accessor_name(), self.reverse_descriptor(self))

    def get_prep_value(self, value):
        if not value is None:
            pk_field = self.target._meta.pk
            return pk_field.get_prep_value(value)
        return None

    def to_python(self, value):
        if not value is None:
            pk_field = self.target._meta.pk
            return pk_field.to_python(value)
        return None

    @property
    def local_related_fields(self):
        return self

    @property
    def foreign_related_fields(self):
        return self.target._meta.pk


class DateTimeField(Field):
    FORMAT = '%Y-%m-%d %H:%M:%S %z'

    def validate(self, value, *args, **kwargs):
        super().validate(value, *args, **kwargs)
        if not value is None and not isinstance(value, datetime):
            raise ValueError('{} must be a datetime object'.format(self.name))

    def get_prep_value(self, value):
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

    def to_python(self, value):
        if not value is None:
            return datetime.strptime(value, self.FORMAT)
        return None


class CreatedAtField(Field):
    def get_attname(self):
        return None

    def contribute_to_class(self, cls, name, *args, **kwargs):
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

    def contribute_to_class(self, cls, name, *args, **kwargs):
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
