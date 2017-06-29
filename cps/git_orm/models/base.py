import copy
from collections import OrderedDict

from django.apps import apps
from django.utils.encoding import force_text

from git_orm import serializer, transaction, GitError
from git_orm.models.options import Options
from git_orm.models.fields import GitToGitForeignKey
from git_orm.models.queryset import QuerySet

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, FieldError


class InvalidObject(Exception):
    pass


MODEL_EXCEPTIONS = (
    ("DoesNotExist", ObjectDoesNotExist),
    ("MultipleObjectsReturned", MultipleObjectsReturned),
    ("InvalidObject", InvalidObject)
)


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

        meta = attrs.pop('Meta', None)

        app_label = None

        app_config = apps.get_containing_app_config(module)

        if getattr(meta, 'app_label', None) is None:
            if app_config is None:
                raise RuntimeError(
                    "Model class %s.%s doesn't declare an explicit "
                    "app_label and isn't in an application in "
                    "INSTALLED_APPS." % (module, cls_name)
                )
            else:
                app_label = app_config.label

        opts = Options(meta, app_label)

        new_class.add_to_class('_meta', opts)

        objects = attrs.pop('objects', None)
        if objects is None:
            objects = QuerySet(new_class)
            for base in bases:
                if not hasattr(base, '_meta'):
                    continue
                if base._meta.has_custom_queryset:
                    objects = base.objects._copy_to_model(cls)
                    new_class._meta.has_custom_queryset = True
                    # TODO: Should we break here?
        else:
            new_class._meta.has_custom_queryset = True
        new_class.add_to_class('objects', objects)

        for name, exc_class in MODEL_EXCEPTIONS:
            exc_class = type(name, (exc_class,), {'__module__': module})
            new_class.add_to_class(name, exc_class)

        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        field_names = [f.name for f in new_class._meta.fields]
        for base in parents:
            if not hasattr(base, '_meta'):
                # Things without _meta aren't functional models, so they're
                # uninteresting parents.
                continue

            parent_fields = base._meta.fields

            # Check for clashes between locally declared fields and those
            # on the base classes (we cannot handle shadowed fields at the
            # moment).
            for field in parent_fields:
                if field.name in field_names:
                    raise FieldError(
                        'Local field %r in class %r clashes '
                        'with field of similar name from '
                        'base class %r' % (field.name, cls_name, base.__name__)
                    )

            for field in parent_fields:
                new_field = copy.deepcopy(field)
                new_class.add_to_class(field.name, new_field)
        new_class._meta.concrete_model = new_class
        opts._prepare()
        new_class._meta.apps.register_model(new_class._meta.app_label, new_class)
        return new_class

    def add_to_class(cls, name, value):
        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


class Model(metaclass=ModelBase):
    _deferred = False

    def __init__(self, **kwargs):
        for field in self._meta.writable_fields:
            attname = field.attname
            if isinstance(field, GitToGitForeignKey):
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

    def dump(self, include_hidden=False, include_pk=True):
        data = OrderedDict()
        for field in self._meta.writable_fields:
            if field.name == self._meta.pk.name and not include_pk:
                continue
            if field.hidden and not include_hidden:
                continue
            value = getattr(self, field.attname)
            data[field.name] = field.get_prep_value(value)
        return serializer.dumps(data)

    def load(self, data):
        try:
            if not hasattr(data, 'items'):
                data = serializer.loads(data)
            for field_name, value in data.items():
                field = self._meta.get_field(field_name)
                setattr(self, field.attname, field.to_python(value))
        except (ValueError, KeyError) as e:
            raise self.InvalidObject(e)

    @property
    def path(self):
        pk = self.pk
        if pk is None:
            raise ValueError('pk must not be None')
        pk = self._meta.pk.get_prep_value(self.pk)
        return [self._meta.storage_name, pk]

    def save(self, *args, **kwargs):
        trans = self._transaction
        serialized = self.dump(include_hidden=True, include_pk=False)
        trans.set_blob(self.path, serialized.encode('utf-8'))
        # TODO: create informative commit message
        trans.add_message('Edit {}'.format(self))

    def delete(self):
        raise NotImplementedError

    @classmethod
    def create(cls, transaction, **kwargs):
        obj = cls(**kwargs)
        obj._transaction = transaction
        obj.save()
        return obj

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        return transaction.list_blobs([cls._meta.storage_name])

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = cls(pk=pk)
        obj._transaction = transaction
        try:
            content = transaction.get_blob(obj.path).decode('utf-8')
        except GitError:
            raise cls.DoesNotExist(
                'object with pk {} does not exist'.format(pk))
        obj.load(content)
        return obj

    def full_clean(self, exclude=None, validate_unique=True):
        if exclude is None:
            exclude = []
        else:
            exclude = list(exclude)
        for field in self._meta.writable_fields:
            if field.name in exclude:
                continue
            try:
                field.validate(getattr(self, field.attname), self)
            except ValueError as e:
                raise self.InvalidObject(e)

    def validate_unique(self, exclude=None):
        return True

    def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        return force_text(dict(field.flatchoices).get(value, value), strings_only=True)

    @classmethod
    def check(cls, **kwargs):
        # TODO: Fill this
        return []

    def serializable_value(self, field_name):
        """
        Returns the value of the field name for this instance. If the field is
        a foreign key, returns the id value, instead of the object. If there's
        no Field object with this name on the model, the model attribute's
        value is returned directly.

        Used to serialize a field's value (in the serializer, or form output,
        for example). Normally, you would just access the attribute directly
        and not use this method.
        """
        try:
            field = self._meta.get_field(field_name)
        except KeyError:
            return getattr(self, field_name)
        return getattr(self, field.attname)
