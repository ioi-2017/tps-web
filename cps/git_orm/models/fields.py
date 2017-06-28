import json
import time
from datetime import datetime, timedelta, timezone

from django.db.models.fields.related import lazy_related_operation
from django.utils.functional import cached_property

from git_orm import transaction

from django.db.models.fields import Field as DjangoField

from git_orm.models.queryset import QuerySet

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
                obj = self.field.target._get_instance(instance._transaction, pk)
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
        if value is not None:
            pk_field = self.target._meta.pk
            return pk_field.get_prep_value(value)
        return None

    def to_python(self, value):
        if value is not None:
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


def create_many_to_many_manager(model, field, reverse):

    class ManyToManyManager(object):
        def __init__(self, instance):
            self.instance = instance
            self.model = model
            if reverse:
                self.related_field_name = field.name
            else:
                self.pk_list = []
            self.instance = instance

        if not reverse:
            def add(self, value):
                if isinstance(value, self.model):
                    self.pk_list.append(value.pk)
                else:
                    self.pk_list.append(value)

            def remove(self, value):
                if isinstance(value, self.model):
                    self.pk_list.remove(value.pk)
                else:
                    self.pk_list.remove(value)

            def get_queryset(self):
                return self.model.objects.with_transaction(self.instance._transaction).filter(pk__in=tuple(self.pk_list))

            def clear(self):
                self.pk_list = []
        else:
            def add(self, value):
                if not isinstance(value, self.model):
                    value = self.model.objects.with_transaction(self.transaction).get(pk=value)
                getattr(value, self.related_field_name).add(self.instance)

            def remove(self, value):
                if not isinstance(value, self.model):
                    value = self.model.objects.with_transaction(self.transaction).get(pk=value)
                getattr(value, self.related_field_name).remove(self.instance)

            def get_queryset(self):
                return self.model.objects.with_transaction(self.instance._transaction).filter(**{
                    self.related_field_name + "__contains": self.instance
                })

            def clear(self):
                objs = list(self)
                for obj in objs:
                    self.remove(obj)

        def __getattr__(self, item):
            if item in ["get", "filter", "exclude", "exists", "count", "order_by", "all"]:
                return getattr(self.get_queryset(), item)
            else:
                raise AttributeError

        def set(self, value):
            self.clear()
            if value is not None:
                for instance in value:
                    self.add(instance)

        def __iter__(self):
            return iter(self.get_queryset())


    return ManyToManyManager


class ManyToManyDescriptor(object):

    def __init__(self, field, reverse):
        self.field = field
        self.reverse = reverse

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
        if self.field.attname not in instance.__dict__:
            instance.__dict__[self.field.attname] = self.related_manager_cls(instance)
        return instance.__dict__[self.field.attname]

    def __set__(self, instance, value):
        """
        Set the related objects through the reverse relation.

        With the example above, when setting ``parent.children = children``:

        - ``self`` is the descriptor managing the ``children`` attribute
        - ``instance`` is the ``parent`` instance
        - ``value`` in the ``children`` sequence on the right of the equal sign
        """
        manager = self.__get__(instance)
        manager.set(value)

    @cached_property
    def related_manager_cls(self):
        model = self.field.model if self.reverse else self.field.target
        return create_many_to_many_manager(
            model,
            self.field,
            self.reverse,
        )


class GitToGitManyToManyField(GitToGitForeignKey):

    def validate(self, value, *args, **kwargs):
        value = self.to_python(value)
        if value is not None:
            for pk in value:
                if not self.target.objects.exists(pk=pk):
                    target_name = self.target.__name__
                    raise ValueError(
                        '{} with pk={!r} does not exist'.format(target_name, pk))

    def get_prep_value(self, value):
        if value is not None:
            pk_field = self.target._meta.pk
            return [pk_field.get_prep_value(pk) for pk in value]
        return None

    def to_python(self, value):
        if value is not None:
            if isinstance(value, str):
                value = json.loads(value)
            if not isinstance(value ,list):
                raise ValueError("{} is not a valid value for M2M field".format(value))
            pk_field = self.target._meta.pk
            return [pk_field.to_python(pk) for pk in value]
        return None

    @staticmethod
    def forward_descriptor(self):
        return ManyToManyDescriptor(self, reverse=False)

    @staticmethod
    def reverse_descriptor(self):
        return ManyToManyDescriptor(self, reverse=True)

    def get_attname(self):
        return self.name