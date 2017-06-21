__version__ = '0.4'
__author__ = 'Martin Natano <natano@natano.net>'


_repository = None
_branch = 'git-orm'
_remote = 'origin'


class GitError(Exception):
    pass


def set_repository(value):
    global _repository
    _repository = value


def get_repository():
    return _repository


def set_branch(value):
    global _branch
    _branch = value


def get_branch():
    return _branch


def set_remote(value):
    global _remote
    _remote = value


def get_remote():
    return _remote
