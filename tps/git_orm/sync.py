from subprocess import Popen

from git_orm import GitError, get_remote, get_branch, get_repository


def fetch():
    cmd = [
        'git', 'fetch', get_remote(),
        'refs/heads/{0}:refs/remotes/origin/{0}'.format(get_branch()),
    ]
    p = Popen(cmd, cwd=get_repository().workdir)
    status = p.wait()
    if status:
        raise GitError('git-fetch returned with exit status {}'.format(status))


def push():
    cmd = [
        'git', 'push', get_remote(),
        'refs/heads/{0}:refs/heads/{0}'.format(get_branch()),
    ]
    p = Popen(cmd, cwd=get_repository().workdir)
    status = p.wait()
    if status:
        raise GitError('git-push returned with exit status {}'.format(status))


def merge():
    raise NotImplementedError
