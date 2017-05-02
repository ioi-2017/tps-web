from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core import serializers
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

import json

__all__ = ["RevisionObject", "Merge", "Conflict", "CloneableMixin"]


class RevisionObjectQuerySet(models.QuerySet):
    def find_matches(self, second_queryset, matching_fields=None):

        if isinstance(second_queryset, models.Manager):
            second_queryset = second_queryset.all()

        if matching_fields is None:
            matching_fields = self.model.get_matching_fields()
        assert len(matching_fields) > 0, "At least one field must be specified for matching"

        pk_name = self.model._meta.pk.name
        constraints = " AND ".join([
            "current.{0}=matched.{0}".format(a if a != "pk" else pk_name) for a in matching_fields
        ])

        current_map = {}
        for obj in self.all():
            current_map[obj.pk] = obj

        other_map = {}
        for obj in second_queryset.all():
            other_map[obj.pk] = obj

        # TODO: Use a benchmark to check if
        # it's faster to handle matching in Python

        from django.db import connection
        with connection.cursor() as c:
            result = []

            # Since some databases(namely sqlite) can't handle
            # full outer joins, we use two left joins instead
            # TODO: we could try using full outer joins and
            # TODO: fallback to this method only if failed

            sql_query = "" \
                        "SELECT current.{pk_name}, matched.{pk_name} FROM ({first_queryset}) current " \
                        "LEFT OUTER JOIN ({second_queryset}) matched ON {join_constraints};" \
                        "".format(first_queryset=str(self.query),
                                  second_queryset=str(second_queryset.query),
                                  pk_name=pk_name,
                                  join_constraints=constraints)
            c.execute(sql_query)
            for a, b in c.fetchall():
                result.append((current_map.get(a, None), other_map.get(b, None)))
            sql_query = "" \
                        "SELECT current.{pk_name}, matched.{pk_name} FROM ({second_queryset}) matched " \
                        "LEFT OUTER JOIN ({first_queryset}) current ON {join_constraints} WHERE current.{pk_name} IS NULL;" \
                        "".format(first_queryset=str(self.query),
                                  second_queryset=str(second_queryset.query),
                                  pk_name=pk_name,
                                  join_constraints=constraints)
            c.execute(sql_query)

            for a, b in c.fetchall():
                result.append((current_map.get(a, None), other_map.get(b, None)))
            return result


class RevisionObjectManager(models.Manager):
    use_for_related_fields = True


class CloneableMixin(object):
    @staticmethod
    def clone_queryset(queryset, cloned_instances, replace_objects=None):
        for obj in queryset.all():
            cloned_instances = obj.clone(cloned_instances=cloned_instances, replace_objects=replace_objects)
        return cloned_instances

    @staticmethod
    def clone_queryset_relations(queryset, cloned_instances):
        for obj in queryset.all():
            obj.clone_relations(cloned_instances=cloned_instances)
        return cloned_instances

    def _clean_for_clone(self, cloned_instances):
        pass

    def clone(self, cloned_instances=None, replace_objects=None):
        if not cloned_instances:
            cloned_instances = {}
        if not replace_objects:
            replace_objects = {}
        if self not in cloned_instances:
            cloned_instances[self] = self.clone_model(self, cloned_instances, replace_objects.get(self, None))
        return cloned_instances

    def clone_relations(self, cloned_instances):
        pass

    @staticmethod
    def clone_model(obj, cloned_instances, previous_object=None):
        new_object = type(obj).objects.get(pk=obj.pk)
        new_object.pk = None if previous_object is None else previous_object.pk
        print(str(new_object.pk) + " X E " + str(new_object))
        new_object._clean_for_clone(cloned_instances=cloned_instances)
        print(str(new_object.pk) + " X E " + str(new_object))
        new_object.save(force_update=(previous_object is not None))
        return new_object


class AbstractModelMeta(ABCMeta, type(models.Model)):
    pass


class RevisionObject(models.Model, CloneableMixin, metaclass=AbstractModelMeta):

    objects = RevisionObjectManager.from_queryset(RevisionObjectQuerySet)()

    def _clean_for_clone(self, cloned_instances):
        super(RevisionObject, self)._clean_for_clone(cloned_instances)
        self.problem = cloned_instances[self.problem]

    @abstractmethod
    def get_value_as_dict(self):
        return get_model_as_dict(self, excluded_fields=["problem"])

    def get_match(self, other_revision):
        matching_data = {
            field: getattr(self, field) for field in self.get_matching_fields()
        }
        matching_data["problem"] = other_revision
        try:
            return type(self).objects.get(**matching_data)
        except self.DoesNotExist:
            return None

    @staticmethod
    @abstractmethod
    def get_matching_fields():
        return ["pk"]

    def matches_with(self, other_object):
        """
        returns a boolean determining whether this matches another_version.
        """
        for field in self.get_matching_fields():
            if getattr(self, field) != getattr(other_object, field):
                return False
        return True

    def diverged_from(self, other_object):
        return self.get_value_as_dict() != other_object.get_value_as_dict()

    @staticmethod
    def differ(version_a, version_b):
        a_none = version_a is None
        b_none = version_b is None
        if a_none != b_none:
            return True
        elif a_none is False:
            return version_a.diverged_from(version_b)
        else:
            return False

    class Meta:
        abstract = True


class Merge(models.Model):
    merged_revision = models.OneToOneField("ProblemRevision", related_name='merge_result')
    our_revision = models.ForeignKey("ProblemRevision", related_name='+')
    their_revision = models.ForeignKey("ProblemRevision", related_name='+')
    base_revision = models.ForeignKey("ProblemRevision", related_name='+', null=True)


class Conflict(models.Model):
    merge = models.ForeignKey(Merge, related_name='conflicts')

    current_content_type = models.ForeignKey(ContentType, null=True, related_name='+')
    current_id = models.PositiveIntegerField(null=True)
    current = GenericForeignKey("current_content_type", "current_id")

    ours_content_type = models.ForeignKey(ContentType, null=True, related_name='+')
    ours_id = models.PositiveIntegerField(null=True)
    ours = GenericForeignKey("theirs_content_type", "ours_id")

    theirs_content_type = models.ForeignKey(ContentType, null=True, related_name='+')
    theirs_id = models.PositiveIntegerField(null=True)
    theirs = GenericForeignKey("ours_content_type", "theirs_id")

    resolved = models.BooleanField(default=False, null=False)

    def __str__(self):
        return "Conflict ({}) -> {}:{}".format(self.content_type, self.ours_id, self.theirs_id)


def get_model_as_dict(obj, included_fields=None, excluded_fields=None):
    """
    Returns a json representation of obj
    including all fields in included_fields (or all fields if not present),
    excluding all fields in excluded_fields (or no fields if not present).
    :param included_fields: List[str] or None
    :param excluded_fields: List[str] or None
    :return str
    """
    full_dump = json.loads(serializers.serialize('json', [obj]))[0]
    if excluded_fields is not None:
        for excluded_field in excluded_fields:
            full_dump['fields'].pop(excluded_field)
    if included_fields is None:
        included_fields = sorted([k for k, v in full_dump['fields'].items()])
    limited_dump = OrderedDict()
    for k in included_fields:
        limited_dump[k] = str(full_dump['fields'][k])
    return limited_dump
