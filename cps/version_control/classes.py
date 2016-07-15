# Amir Keivan Mohtashami


class Version(object):

    def get_json_representation(self):
        """
        Returns a json representation of the current versions,
        including all fields in _meta.json_included_fields (or all fields if not present),
        excluding all fields in _meta.json_excluded_fields (or no fields if not present).
        """

        raise NotImplementedError("This must be implemented")

    def diff(self, another_version):
        """
        Returns diff of this version and another_version.
        By default, it will output produced by executing diff on JSON representation
        of the two versions returned by get_json_representation.
        It may be overridden in the subclasses to produce different outputs.
        """

        raise NotImplementedError("This must be implemented")

    def clone(self):
        raise NotImplementedError("This must be implemented in the subclasses of this class")

    def matches(self, another_version):
        """
        returns a boolean determining whether this matches another_version.
        """
        raise NotImplementedError("This must be implemented in the subclasses of this class")

    def matching_bucket(self):
        """
        returns the bucket used for matching. use this method to speed up the matching process when number of objects
        in the same revision and of the same type is too large. you may return None to put all objects in the same
        bucket.
        """
        return None