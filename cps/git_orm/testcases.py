import shutil
import stat
from tempfile import mkdtemp

from nose.tools import eq_, ok_, assert_in
import pygit2

from git_orm import set_repository, get_branch


class GitTestCase:
    def setup(self):
        self.repo = pygit2.init_repository(mkdtemp(), False)
        set_repository(self.repo.path)
        self.branchref = 'refs/heads/{}'.format(get_branch())
        self.assert_commit_count(0)

    def teardown(self):
        shutil.rmtree(self.repo.workdir)

    def assert_file_exists(self, filename):
        tree = self.repo.lookup_reference(self.branchref).get_object().tree
        *path, filename = filename.split('/')
        for name in path:
            assert_in(name, tree)
            entry = tree[name]
            ok_(entry.filemode & stat.S_IFDIR)
            tree = self.repo[entry.oid]
        assert_in(filename, tree)
        entry = tree[filename]
        ok_(entry.filemode & stat.S_IFREG)

    def assert_commit_count(self, expected_count):
        try:
            oid = self.repo.lookup_reference(self.branchref).target
        except KeyError:
            count = 0
        else:
            count = sum(1 for _ in self.repo.walk(oid, pygit2.GIT_SORT_NONE))
        eq_(count, expected_count)
