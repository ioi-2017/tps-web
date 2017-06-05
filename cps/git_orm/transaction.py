import stat
from functools import wraps
from collections import namedtuple
from datetime import datetime, timezone, timedelta

import pygit2

from git_orm import GitError, get_repository, get_branch
from git_orm.quote import quote_filename, unquote_filename


MemoryTree = namedtuple('MemoryTree', ['tree', 'childs', 'blobs'])
FileStat = namedtuple('FileStat', ['created_at', 'updated_at'])


class Transaction:
    def __init__(self, repo, parents):
        self.repo = repo

        self.parents = parents
        tree = []
        if parents:
            tree = repo[parents[0]].tree
        self.memory_tree = MemoryTree(tree, {}, {})

        self.has_changes = False
        self.messages = []

    def get_memory_tree(self, path):
        memory_tree = self.memory_tree
        for name in path:
            if not name in memory_tree.childs:
                tree = []
                if name in memory_tree.tree:
                    entry = memory_tree.tree[name]
                    if entry.filemode & stat.S_IFDIR:
                        tree = self.repo[entry.oid]
                memory_tree.childs[name] = MemoryTree(tree, {}, {})
            memory_tree = memory_tree.childs[name]
        return memory_tree

    def exists(self, path):
        *path, filename = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        for files in (memory_tree.blobs, memory_tree.childs, memory_tree.tree):
            if filename in files:
                return True
        return False

    def get_blob(self, path):
        *path, filename = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        content = None
        if filename in memory_tree.blobs:
            content = memory_tree.blobs[filename]
        elif filename in memory_tree.tree:
            entry = memory_tree.tree[filename]
            if entry.filemode & stat.S_IFREG:
                content = self.repo[entry.oid].data
        if content is None:
            raise GitError('blob not found')
        return content

    def set_blob(self, path, content):
        *path, filename = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        memory_tree.blobs[filename] = content
        self.has_changes = True

    def list_blobs(self, path):
        path = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        names = set(memory_tree.blobs.keys())
        for entry in memory_tree.tree:
            if entry.filemode & stat.S_IFREG:
                names.add(entry.name)
        return set(map(unquote_filename, names))

    def walk(self, reverse=False):
        sort = pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME
        if not reverse:
            sort |= pygit2.GIT_SORT_REVERSE     # sic
        # FIXME: only works for transactions with exactly one parent
        return self.repo.walk(self.parents[0], sort)

    def stat(self, path):
        *path, filename = map(quote_filename, path)
        created_at = updated_at = None
        previous_oid = None
        for commit in self.walk():
            tree = commit.tree
            try:
                for part in path:
                    tree = self.repo[tree[part].oid]
                entry = self.repo[tree[filename].oid]
            except KeyError:
                continue
            if not previous_oid == entry.oid:
                updated_at = datetime.fromtimestamp(
                    commit.commit_time,
                    timezone(timedelta(minutes=commit.commit_time_offset)))
                if previous_oid is None:
                    created_at = updated_at
                previous_oid = commit.oid
        return FileStat(created_at, updated_at)

    def add_message(self, message):
        self.messages += [message]

    def _store_objects(self, memory_tree):
        treebuilder = self.repo.TreeBuilder()
        for entry in memory_tree.tree:
            treebuilder.insert(entry.name, entry.oid, entry.filemode)
        for name, content in memory_tree.blobs.items():
            blob_id = self.repo.create_blob(content)
            treebuilder.insert(name, blob_id, stat.S_IFREG | 0o644)
        for name, child in memory_tree.childs.items():
            if not child.childs and not child.blobs:
                continue
            tree_id = self._store_objects(child)
            treebuilder.insert(name, tree_id, stat.S_IFDIR)
        return treebuilder.write()

    def commit(self, message=None):
        if not self.has_changes:
            raise GitError(
                'nothing changed; use rollback to abort the transaction')
        if not message:
            if not self.messages:
                raise GitError('no message for commit')
            message = '\n'.join(self.messages)
        elif self.messages:
            message += '\n\n' + '\n'.join(self.messages)

        tree_id = self._store_objects(self.memory_tree)

        try:
            name = self.repo.config['user.name']
            email = self.repo.config['user.email']
        except KeyError as e:
            raise GitError('{} not found in git config'.format(e))
        sig = pygit2.Signature(name, email)
        ref = 'refs/heads/{}'.format(get_branch())
        self.repo.create_commit(
            ref, sig, sig, message, tree_id, self.parents, 'utf-8')

    def rollback(self):
        self.memory_tree = {}
        self.messages = []


_transaction = None


def begin():
    global _transaction
    if _transaction:
        raise GitError('there is already a transaction running')
    repo = get_repository()
    if repo is None:
        raise GitError('no repository found')
    ref = 'refs/heads/{}'.format(get_branch())
    try:
        parents = [repo.lookup_reference(ref).target]
    except KeyError:
        parents = []
    _transaction = Transaction(repo, parents)


def commit(message=None):
    global _transaction
    if not _transaction:
        raise GitError('no transaction in progress')
    _transaction.commit(message)
    _transaction = None


def rollback():
    global _transaction
    if not _transaction:
        raise GitError('no transaction in progress')
    _transaction.rollback()
    _transaction = None


def current():
    if _transaction is None:
        raise GitError('no transaction running')
    return _transaction


class wrap:
    def __init__(self, message=None):
        self.message = message

    def __call__(self, fn):
        @wraps(fn)
        def _inner(*args, **kwargs):
            with self:
                return fn(*args, **kwargs)
        return _inner

    def __enter__(self):
        self.active = not _transaction
        if self.active:
            begin()
        return _transaction

    def __exit__(self, type, value, traceback):
        if self.active:
            if not type and _transaction.has_changes:
                commit(self.message)
            else:
                rollback()
