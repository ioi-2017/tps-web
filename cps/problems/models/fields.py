import json

import six
from django import forms
from django.db import models
from django.db import router
from django.db import transaction
from django.db.models.fields.related import lazy_related_operation
from django.utils.functional import cached_property, curry

from git_orm.models import GitToGitForeignKey
from git_orm.models.fields import ReverseForeignKeyDescriptor, create_many_to_many_manager, ManyToManyDescriptor
from git_orm.transaction import Transaction



def create_git_related_manager(superclass, field):
    """
    Factory function to create a manager that subclasses another manager
    (generally the default manager of a given model) and adds behaviors
    specific to generic relations.
    """

    class ProblemGitRelatedObjectManager(superclass):
        def __init__(self, instance=None):
            from problems.models.problem import Problem
            super(ProblemGitRelatedObjectManager, self).__init__()

            self.instance = instance

            self.model = field.model

            self.problem = Problem.objects.get(repository_path=instance._transaction.repo.path)
            self.commit_id = str(instance._transaction.parents[0])
            self.commit_id_field_name = field.commit_id_field_name
            self.problem_field_name = field.problem_field_name
            self.prefetch_cache_name = field.attname

            self.core_filters = {
                '%s__pk' % self.problem_field_name: self.problem.pk,
                self.commit_id_field_name: self.commit_id,
            }

        def __call__(self, **kwargs):
            # We use **kwargs rather than a kwarg argument to enforce the
            # `manager='manager_name'` syntax.
            manager = getattr(self.model, kwargs.pop('manager'))
            manager_class = create_git_related_manager(manager.__class__, field)
            return manager_class(instance=self.instance)
        do_not_call_in_templates = True

        def __str__(self):
            return repr(self)

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[self.prefetch_cache_name]
            except (AttributeError, KeyError):
                db = self._db or router.db_for_read(self.model)
                return super(ProblemGitRelatedObjectManager, self).get_queryset().using(db).filter(**self.core_filters)

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = super(ProblemGitRelatedObjectManager, self).get_queryset()

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)

            query = {
                '%s__pk' % self.problem_field_name: self.problem.pk,
                '%s__in' % self.commit_id_field_name: set(obj._get_pk_val() for obj in instances)
            }

            # We (possibly) need to convert object IDs to the type of the
            # instances' PK in order to match up instances:
            object_id_converter = instances[0]._meta.pk.to_python
            return (queryset.filter(**query),
                    lambda relobj: object_id_converter(getattr(relobj, self.object_id_field_name)),
                    lambda obj: obj._get_pk_val(),
                    False,
                    self.prefetch_cache_name)

        def add(self, *objs, **kwargs):
            bulk = kwargs.pop('bulk', True)
            db = router.db_for_write(self.model)

            def check_and_update_obj(obj):
                if not isinstance(obj, self.model):
                    raise TypeError("'%s' instance expected, got %r" % (
                        self.model._meta.object_name, obj
                    ))
                setattr(obj, self.content_type_field_name, self.content_type)
                setattr(obj, self.object_id_field_name, self.pk_val)

            if bulk:
                pks = []
                for obj in objs:
                    if obj._state.adding or obj._state.db != db:
                        raise ValueError(
                            "%r instance isn't saved. Use bulk=False or save "
                            "the object first." % obj
                        )
                    check_and_update_obj(obj)
                    pks.append(obj.pk)

                self.model._base_manager.using(db).filter(pk__in=pks).update(**self.core_filters)
            else:
                with transaction.atomic(using=db, savepoint=False):
                    for obj in objs:
                        check_and_update_obj(obj)
                        obj.save()
        add.alters_data = True

        def remove(self, *objs, **kwargs):
            if not objs:
                return
            bulk = kwargs.pop('bulk', True)
            self._clear(self.filter(pk__in=[o.pk for o in objs]), bulk)
        remove.alters_data = True

        def clear(self, **kwargs):
            bulk = kwargs.pop('bulk', True)
            self._clear(self, bulk)
        clear.alters_data = True

        def _clear(self, queryset, bulk):
            db = router.db_for_write(self.model)
            queryset = queryset.using(db)
            if bulk:
                # `QuerySet.delete()` creates its own atomic block which
                # contains the `pre_delete` and `post_delete` signal handlers.
                queryset.delete()
            else:
                with transaction.atomic(using=db, savepoint=False):
                    for obj in queryset:
                        obj.delete()
        _clear.alters_data = True

        def set(self, objs, **kwargs):
            # Force evaluation of `objs` in case it's a queryset whose value
            # could be affected by `manager.clear()`. Refs #19816.
            objs = tuple(objs)

            bulk = kwargs.pop('bulk', True)
            clear = kwargs.pop('clear', False)

            db = router.db_for_write(self.model)
            with transaction.atomic(using=db, savepoint=False):
                if clear:
                    self.clear()
                    self.add(*objs, bulk=bulk)
                else:
                    old_objs = set(self.using(db).all())
                    new_objs = []
                    for obj in objs:
                        if obj in old_objs:
                            old_objs.remove(obj)
                        else:
                            new_objs.append(obj)

                    self.remove(*old_objs)
                    self.add(*new_objs, bulk=bulk)
        set.alters_data = True

        def create(self, **kwargs):
            kwargs[self.commit_id_field_name] = self.commit_id
            kwargs[self.problem_field_name] = self.problem
            db = router.db_for_write(self.model)
            return super(ProblemGitRelatedObjectManager, self).using(db).create(**kwargs)
        create.alters_data = True

        def get_or_create(self, **kwargs):
            kwargs[self.commit_id_field_name] = self.commit_id
            kwargs[self.problem_field_name] = self.problem
            db = router.db_for_write(self.model)
            return super(ProblemGitRelatedObjectManager, self).using(db).get_or_create(**kwargs)
        get_or_create.alters_data = True

        def update_or_create(self, **kwargs):
            kwargs[self.commit_id_field_name] = self.commit_id
            kwargs[self.problem_field_name] = self.problem
            db = router.db_for_write(self.model)
            return super(ProblemGitRelatedObjectManager, self).using(db).update_or_create(**kwargs)
        update_or_create.alters_data = True

    return ProblemGitRelatedObjectManager


class ReverseGitManyToOneDescriptor(object):
    """
    Accessor to the related objects manager on the reverse side of a
    many-to-one relation.

    In the example::

        class Child(Model):
            parent = ForeignKey(Parent, related_name='children')

    ``parent.children`` is a ``ReverseManyToOneDescriptor`` instance.

    Most of the implementation is delegated to a dynamically defined manager
    class built by ``create_forward_many_to_many_manager()`` defined below.
    """

    def __init__(self, field):
        self.field = field

    @cached_property
    def related_manager_cls(self):
        return create_git_related_manager(
            self.field.model._default_manager.__class__,
            self.field,
        )

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

        return self.related_manager_cls(instance)

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


class DBToGitForeignKeyDescriptor(object):
    def __init__(self, field):
        self.field = field
        self.commit_id_field_name = field.commit_id_field_name
        self.problem_field_name = field.problem_field_name

    def get_cache_name(self):
        return '_cache_%s' % self.field.attname

    def __get__(self, instance, owner):
        if instance is None:
            return self
        repository_path = getattr(instance, self.problem_field_name).repository_path
        commit_id = getattr(instance, self.commit_id_field_name)
        if not hasattr(instance, self.get_cache_name()):
            pk = getattr(instance, self.field.attname, self.field.get_default())
            git_transaction = Transaction(
                repository_path=repository_path,
                commit_id=commit_id
            )
            if pk is None:
                obj = None
            else:
                obj = self.field.target.objects.with_transaction(git_transaction).get(pk=pk)
            setattr(instance, self.get_cache_name(), obj)
        return getattr(instance, self.get_cache_name())

    def __set__(self, instance, value):
        if isinstance(value, self.field.target):
            pk = value.pk
            setattr(instance, self.get_cache_name(), value)
        else:
            pk = value
            try:
                delattr(instance, self.get_cache_name())
            except AttributeError:
                pass
        setattr(instance, self.field.attname, pk)


class DBToGitForeignKey(GitToGitForeignKey):
    # TODO: Make this a proper Django field
    forward_descriptor = DBToGitForeignKeyDescriptor
    reverse_descriptor = ReverseGitManyToOneDescriptor

    def __init__(self, to, problem_field_name, commit_id_field_name, *args, **kwargs):
        super(DBToGitForeignKey, self).__init__(to, *args, **kwargs)
        self.max_length = 128
        self.problem_field_name = problem_field_name
        self.commit_id_field_name = commit_id_field_name

    def deconstruct(self):
        name, path, args, kwargs = super(DBToGitForeignKey, self).deconstruct()
        if isinstance(self.target, six.string_types):
            kwargs['to'] = self.target
        else:
            kwargs['to'] = "%s.%s" % (
                self.target._meta.app_label,
                self.target._meta.object_name,
            )
        kwargs["problem_field_name"] = self.problem_field_name
        kwargs["commit_id_field_name"] = self.commit_id_field_name
        return name, path, args, kwargs

    def get_internal_type(self):
        return "CharField"


class DBToGitReadOnlyForeignKey(DBToGitForeignKey):
    def set_attributes_from_name(self, name):
        if not self.name:
            self.name = name
        self.attname, self.column = self.get_attname_column()
        self.concrete = False
        if self.verbose_name is None and self.name:
            self.verbose_name = self.name.replace('_', ' ')

    def contribute_to_class(self, cls, name, virtual_only=True):
        self.set_attributes_from_name(name)
        self.model = cls
        if virtual_only:
            cls._meta.add_field(self, virtual=True)
        else:
            cls._meta.add_field(self)
        if self.choices:
            setattr(cls, 'get_%s_display' % self.name,
                    curry(cls._get_FIELD_display, field=self))
        setattr(cls, self.name, self.forward_descriptor(self))

        def resolve_related_class(model, related, field):
            field.target = related
            field.do_related_class(related, model)

        lazy_related_operation(resolve_related_class, cls, self.target, field=self)


class ReadOnlyDescriptor(object):

    def __init__(self, attr, default):
        self.attr = attr
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        method_name = "get_{}".format(self.attr)
        return getattr(instance, method_name, self.default)

    def __set__(self, instance, value):
        pass


class ReadOnlyGitToGitForeignKey(GitToGitForeignKey):
    # TODO: Make sure this is not written in dump
    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(ReadOnlyGitToGitForeignKey, self).contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, self.attname, ReadOnlyDescriptor(self.attname, self.get_default()))


def create_db_to_git_many_to_many_manager(problem_field, commit_field, *args, **kwargs):

    cls = create_many_to_many_manager(*args, **kwargs)

    class ManyToManyManager(cls):
        @cached_property
        def transaction(self):
            repository_path = getattr(self.instance, problem_field).repository_path
            commit_id = getattr(self.instance, commit_field)
            return Transaction(
                repository_path=repository_path,
                commit_id=commit_id
            )

    return ManyToManyManager


class DBToGitManyToManyDescriptor(ManyToManyDescriptor):

    def __init__(self, field):
        super(DBToGitManyToManyDescriptor, self).__init__(field, reverse=False)

    @cached_property
    def related_manager_cls(self):
        return create_db_to_git_many_to_many_manager(
            self.field.problem_field_name,
            self.field.commit_id_field_name,
            self.field.to,
            self.field,
            False,
        )


class DBToGitManyToManyField(models.TextField):

    def __init__(self, to, problem_field_name, commit_id_field_name, *args, **kwargs):
        super(DBToGitManyToManyField, self).__init__(*args, **kwargs)
        self.to = to
        self.problem_field_name = problem_field_name
        self.commit_id_field_name = commit_id_field_name

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(DBToGitManyToManyField, self).contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, DBToGitManyToManyDescriptor(self))

        def resolve_related_class(model, related, field):
            field.target = related
            # TODO: Support backward relation
        lazy_related_operation(resolve_related_class, cls, self.to, field=self)

    def get_prep_value(self, value):
        if isinstance(value, str):
            return value
        elif hasattr(value, 'all'):
            pk_list = [obj.pk for obj in value.all()]
        else:
            pk_list = list(value)
        value = json.dumps(pk_list)
        return value

    def to_python(self, value):
        if isinstance(value, str):
            return json.loads(value)
        else:
            return value

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def deconstruct(self):
        name, path, args, kwargs = super(DBToGitManyToManyField, self).deconstruct()
        kwargs["to"] = self.to
        kwargs["problem_field_name"] = self.problem_field_name
        kwargs["commit_id_field_name"] = self.commit_id_field_name
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.ModelMultipleChoiceField,
            'queryset': self.target.objects,
        }
        defaults.update(kwargs)
        if defaults.get('initial') is not None:
            initial = defaults['initial']
            if callable(initial):
                initial = initial()
            defaults['initial'] = [i.pk for i in initial]
        return super(models.TextField, self).formfield(**defaults)


