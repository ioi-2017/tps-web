from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core import serializers

import json

__all__ = ["RevisionObject", "Merge", "Conflict"]


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


class RevisionObject(models.Model):

    objects = RevisionObjectManager.from_queryset(RevisionObjectQuerySet)()

    def _get_json_representation(self, included_fields=None, excluded_fields=None):
        """
        Returns a json representation of the current version,
        including all fields in included_fields (or all fields if not present),
        excluding all fields in excluded_fields (or no fields if not present).
        :param included_fields: List[str] or None
        :param excluded_fields: List[str] or None
        :return str
        """
        full_dump = json.loads(serializers.serialize('json', [self]))[0]
        limited_dump = {}
        for field_name in full_dump['fields']:
            if included_fields is not None and field_name not in included_fields:
                continue
            if excluded_fields is not None and field_name in excluded_fields:
                continue
            limited_dump[field_name] = full_dump['fields'][field_name]
        return json.dumps(limited_dump)

    def get_json_representation(self):
        return self._get_json_representation()

    def diff(self, other_object):
        """
        Returns diff of this version and another_version in HTML format.
        By default, it will output produced by executing diff on JSON representation
        of the two versions returned by get_json_representation.
        It may be overridden in the subclasses to produce different outputs.
        :param another_version: Version
        :return str
        """
        import difflib
        return difflib.HtmlDiff(tabsize=4, wrapcolumn=80).make_table(
            self.get_json_representation(),
            other_object.get_json_representation()
        )

    @staticmethod
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
        our_json = json.loads(self.get_json_representation())
        their_json = json.loads(other_object.get_json_representation())
        return our_json == their_json

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
    merged_revision = models.ForeignKey("ProblemRevision", related_name='merges')
    our_revision = models.ForeignKey("ProblemRevision", related_name='+')
    their_revision = models.ForeignKey("ProblemRevision", related_name='+')
    base_revision = models.ForeignKey("ProblemRevision", related_name='+')


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