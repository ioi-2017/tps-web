# Amir Keivan Mohtashami

from django.db import models
from version_control.classes import Version


class Revision(models.Model):
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

    def find_matching_pairs(self, second_revision: Revision):
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

    def clone(self):
        raise NotImplementedError("This must be implemented in the subclasses of this class")

    def save(self, *args, **kwargs):
        if self.parent_revision:
            self.depth = self.parent_revision.depth + 1
        else:
            self.depth = 1
        super(Revision, self).save(*args, **kwargs)


class VersionModel(models.Model, Version):

    class Meta:
        abstract = True