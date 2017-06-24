import six
from django.db import router
from django.db import transaction
from django.utils.functional import cached_property

from git_orm.models import GitToGitForeignKey
from git_orm.models.fields import ReverseForeignKeyDescriptor
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

            self.model = field.target

            self.problem = Problem.objects.get(repository_path=instance._transaction.repo.path)
            self.commit_id = instance._transaction.commit_id
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
                db = self._db or router.db_for_read(self.model, instance=self.instance)
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
            db = router.db_for_write(self.model, instance=self.instance)

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
            db = router.db_for_write(self.model, instance=self.instance)
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

            db = router.db_for_write(self.model, instance=self.instance)
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
            db = router.db_for_write(self.model, instance=self.instance)
            return super(ProblemGitRelatedObjectManager, self).using(db).create(**kwargs)
        create.alters_data = True

        def get_or_create(self, **kwargs):
            kwargs[self.commit_id_field_name] = self.commit_id
            kwargs[self.problem_field_name] = self.problem
            db = router.db_for_write(self.model, instance=self.instance)
            return super(ProblemGitRelatedObjectManager, self).using(db).get_or_create(**kwargs)
        get_or_create.alters_data = True

        def update_or_create(self, **kwargs):
            kwargs[self.commit_id_field_name] = self.commit_id
            kwargs[self.problem_field_name] = self.problem
            db = router.db_for_write(self.model, instance=self.instance)
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
            self.field.target._default_manager.__class__,
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


    def __get__(self, instance, owner):
        if instance is None:
            return self
        repository_path = getattr(instance, self.problem_field_name).repo.path
        commit_id = getattr(instance, self.commit_id_field_name)
        if not hasattr(self, '_cache'):
            pk = getattr(instance, self.field.attname)
            git_transaction = Transaction(
                repository_path=repository_path,
                commit_id=commit_id
            )
            if pk is None:
                obj = None
            else:
                obj = self.field.target.objects.with_transaction(git_transaction).get(pk=pk)
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


class DBToGitForeignKey(GitToGitForeignKey):
    forward_descriptor = DBToGitForeignKeyDescriptor
    reverse_descriptor = ReverseGitManyToOneDescriptor

    def __init__(self, to, problem_field_name, commit_id_field_name, *args, **kwargs):
        super(DBToGitForeignKey, self).__init__(to, *args, **kwargs)
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
    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(ReadOnlyGitToGitForeignKey, self).contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, self.attname, ReadOnlyDescriptor(self.attname, self.get_default()))
