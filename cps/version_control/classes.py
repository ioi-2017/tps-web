__author__ = 'akm'


class Version(object):

    def get_differences(self, another_version):
        raise NotImplementedError("This must be implemented in the subclasses of this class")

    def clone(self):
        raise NotImplementedError("This must be implemented in the subclasses of this class")