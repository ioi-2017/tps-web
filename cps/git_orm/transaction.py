import os
import stat
from functools import wraps
from collections import namedtuple
from datetime import datetime, timezone, timedelta
from pathlib import PurePath

import pygit2

from git_orm import GitError, get_repository, get_branch
from git_orm.quote import quote_filename, unquote_filename

from django.conf import settings


MemoryTree = namedtuple('MemoryTree', ['tree', 'childs', 'blobs'])
FileStat = namedtuple('FileStat', ['created_at', 'updated_at'])


def get_branch_reference(name):
    return 'refs/heads/{}'.format(name)


class Transaction:
    def __init__(self, repository_path, commit_id=None, branch_name=None):
        try:
            path = pygit2.discover_repository(repository_path)
        except KeyError:
            raise GitError('no repository found in "{}"'.format(repository_path))
        self.repo = repo = pygit2.Repository(path)

        if branch_name is not None and commit_id is not None:
            raise ValueError('only one of branch_name and commit_id should be set')

        if branch_name is None and commit_id is None:
            raise ValueError('either branch_name or commit_id should be set')

        if branch_name is not None:
            self.branch = branch_name
            branch_reference = get_branch_reference(self.branch)
            try:
                commit_oid = self.repo.lookup_reference(branch_reference).target
            except KeyError:
                parents = []
            else:
                parents = [commit_oid]
        else:
            commit_oid = pygit2.Oid(hex=commit_id)
            parents = [commit_oid]

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
        path = PurePath(os.path.join(*path)).parts
        *path, filename = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        for files in (memory_tree.blobs, memory_tree.childs, memory_tree.tree):
            if filename in files:
                return True
        return False

    def get_blob(self, path):
        path = PurePath(os.path.join(*path)).parts
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
        path = PurePath(os.path.join(*path)).parts
        *path, filename = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        memory_tree.blobs[filename] = content
        self.has_changes = True

    def list_blobs(self, path, recursive=False):
        path = map(quote_filename, path)
        memory_tree = self.get_memory_tree(path)
        names = set(memory_tree.blobs.keys())
        trees = [(memory_tree.tree, [])]
        for tree, path_prefix in trees:
            for entry in tree:
                if entry.filemode & stat.S_IFREG:
                    names.add(os.path.join(*path_prefix, entry.name))
                elif recursive:
                    if entry.filemode & stat.S_IFDIR:
                        trees.append((self.repo[entry.oid], path_prefix + [entry.name]))
        return set(map(unquote_filename, names))

    def walk(self, reverse=False):
        sort = pygit2.GIT_SORT_TOPOLOGICAL | pygit2.GIT_SORT_TIME
        if not reverse:
            sort |= pygit2.GIT_SORT_REVERSE     # sic
        # FIXME: only works for transactions with exactly one parent
        return self.repo.walk(self.parents[0], sort)

    def stat(self, path):
        path = PurePath(os.path.join(*path)).parts
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

    def commit(self, message=None, author_signature=None, amend=False, allow_empty=False):
        if not self.branch:
            raise GitError('no branch specified')
        if not allow_empty and not self.has_changes:
            raise GitError(
                'nothing changed; use rollback to abort the transaction')
        if amend:
            if len(self.parents) > 1:
                raise GitError('cannot amend more than one commit')
            elif len(self.parents) == 0:
                raise GitError('no commit to amend')
            else:
                previous_commit_message = self.repo[self.parents[0]].message
                parts = previous_commit_message.split('\n\n')
                if not message:
                    message = parts[0]
                detailed_messages = ['\n\n'.join(parts[1:])] + self.messages
            parents = self.repo[self.parents[0]].parents
        else:
            detailed_messages = self.messages
            if not message:
                if not self.messages:
                    raise GitError('no message for commit')
                message = '\n'.join(detailed_messages)
            parents = self.parents
        if detailed_messages:
            message += '\n\n' + '\n'.join(detailed_messages)

        tree_id = self._store_objects(self.memory_tree)

        try:
            name = settings.GIT_USER_NAME
            email = settings.GIT_USER_EMAIL
        except KeyError as e:
            raise GitError('{} not found in Django settings'.format(e))
        sig = pygit2.Signature(name, email)
        if not author_signature:
            author_signature = sig
        ref = get_branch_reference(self.branch)
        self.repo.create_commit(
            ref, author_signature, sig, message, tree_id, parents, 'utf-8')

    def rollback(self):
        self.memory_tree = {}
        self.messages = []


_transaction = None


def set_default_transaction(transaction):
    global _transaction
    _transaction = transaction


def begin():
    global _transaction
    if _transaction:
        raise GitError('there is already a transaction running')
    _transaction = Transaction(repository_path=get_repository(), branch_name=get_branch())


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
