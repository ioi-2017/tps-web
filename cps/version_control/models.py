from django.db import models
from version_control.classes import Version

# TODO: This might be
# useful in cloning models http://stackoverflow.com/questions/2233883/get-all-related-django-model-objects
# FIXME: DELETE THIS


class Revision(models.Model):

    REQUIRED_ATTRIBUTES = ["parent_revision", "depth"]

    class Meta:
        abstract = True

    @property
    def related_objects(self):
        """
        This method returns all objects that are part of this revision
        """
        raise NotImplementedError("This must be implemented in the subclasses of this class")

    def get_differences(self, another_revision):
        """
        returns a list of pairs (a, b) which means
         in this revision an object is a and its corresponding object in another_revision is b.
         if b is None, a is a new object.
         if a is None, b has been deleted.
        """
        raise NotImplementedError("This must be implemented in the subclasses of this class")

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