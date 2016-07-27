# Amir Keivan Mohtashami
# Mohammad Roghani

from copy import copy

from django.db import models

from version_control.classes import Version


class CloneableModel(models.Model):
    def get_all_neighbor_objects(self):
        """
        find all objects that are adjacent to specific object
        """
        return_list = []
        for field in self._meta.get_fields():
            if field.is_relation:
                if field.many_to_one or field.one_to_one:
                    fld = getattr(self, field.name)
                    return_list.append(fld)
                else:
                    field_name = field.name
                    if field.auto_created:
                        if field.related_name is not None:
                            field_name = field.related_name
                        else:
                            field_name += "_set"
                    for fld in getattr(self, field_name).all():
                        return_list.append(fld)
        return return_list

    def clone(self, ignore_list):
        """
        make copy of every objects that are related to one object
        """
        old_objects = self.get_all_related_object()
        new_objects = []
        old_to_new_objects_map = {}
        new_to_old_objects_map = {}
        for old_object in old_objects:
            if type(old_object) in ignore_list:
                new_objects.append(None)
                old_to_new_objects_map.update({(old_object, old_object)})
                new_to_old_objects_map.update({(old_object, old_object)})

            else:
                new_object = copy(old_object)
                new_object.id = None
                new_object.save()
                new_objects.append(new_object)
                old_to_new_objects_map.update({(old_object, new_object)})
                new_to_old_objects_map.update({(new_object, old_object)})
        for new_object in new_objects:
            if new_object is not None:
                for field in new_object._meta.get_fields():
                    if field.is_relation and (field.many_to_one or field.one_to_one):
                        setattr(new_object, field.name, old_to_new_objects_map[getattr(new_object, field.name)])
                        new_object.save()

        for new_object in new_objects:
            if new_object is not None:
                for field in new_object._meta.get_fields():
                    if field.is_relation and field.many_to_many and field.auto_created is False:
                        for fld in getattr(new_to_old_objects_map[new_object], field.name).all():
                            if old_to_new_objects_map[fld] not in getattr(new_object, field.name).all():
                                getattr(new_object, field.name).add(old_to_new_objects_map[fld])
                                new_object.save()
        return old_to_new_objects_map[self]

    def get_all_related_object(self):
        """
        find all object that are related to one object
        """
        mark = set([])
        return self._get_all_related_object_recursively(mark)

    def _get_all_related_object_recursively(self, mark):
        """
        recursively go to adjacent objects of an object and find related objects
        it works like dfs
        """
        mark.update([(self.__class__, self.id)])
        return_list = [self]
        neighbors = self.get_all_neighbor_objects()
        for fld in neighbors:
            if isinstance(fld, VersionModel) and (fld.__class__, fld.pk) not in mark:
                return_list.extend(fld._get_all_related_object_recursively(mark))
        return return_list

    class Meta:
        abstract = True


class VersionModel(CloneableModel, Version):

    class Meta:
        abstract = True


class Revision(CloneableModel):
    """
    Every revision may have a ForeignKey to its previous revision called parent_revision. An integer field called depth,
    will be automatically filled with the number of previous revisions in the current revision chain.
    """

    class Meta:
        abstract = True

    def get_related_objects(self):
        """
        This method returns all objects that are part of this revision
        """
        # TODO: This might be
        # useful http://stackoverflow.com/questions/2233883/get-all-related-django-model-objects
        # FIXME: DELETE THIS

        raise NotImplementedError("This must be implemented in the subclasses of this class")

    def find_matching_pairs(self, second_revision):
        """
        returns a list of pairs (a, b) which means
         in this revision an object is a and its corresponding object in another_revision is b.
         if b is None, a is a new object.
         if a is None, b has been deleted.
        """

        def group_by_buckets(objects):
            bucketed_objects = {}
            for obj in objects:
                class_type = obj.__class__
                if class_type not in bucketed_objects:
                    bucketed_objects[class_type] = {}
                if obj.matching_bucket not in bucketed_objects[class_type]:
                    bucketed_objects[class_type][obj.matching_bucket] = []
                bucketed_objects[class_type][obj.matching_bucket].append(obj)
            return bucketed_objects

        my_objects = group_by_buckets(self.get_related_objects())
        other_objects = group_by_buckets(second_revision.get_related_objects())

        # TODO: iterate through buckets and find matches

        raise NotImplementedError("This must be implemented")

    def save(self, *args, **kwargs):
        if self.parent_revision:
            self.depth = self.parent_revision.depth + 1
        else:
            self.depth = 1
        super(Revision, self).save(*args, **kwargs)