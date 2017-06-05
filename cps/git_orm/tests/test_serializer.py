from nose.tools import *

from git_orm.serializer import dumps, loads


class TestDump:
    def test_none(self):
        s = dumps({'none': None})
        eq_(s, 'none: \n')

    def test_oneline(self):
        s = dumps({'oneline': 'foo'})
        eq_(s, 'oneline: foo\n')

    def test_multiline(self):
        s = dumps({'multiline': 'foo\nbar\nbaz'})
        eq_(s, 'multiline: foo\n    bar\n    baz\n')


class TestLoad:
    def test_none(self):
        data = loads('none: ')
        eq_(len(data), 1)
        eq_(data['none'], None)

    def test_oneline(self):
        data = loads('oneline: foo')
        eq_(len(data), 1)
        eq_(data['oneline'], 'foo')

    def test_multiline(self):
        data = loads('multiline: foo\n    bar\n    baz')
        eq_(len(data), 1)
        eq_(data['multiline'], 'foo\nbar\nbaz')

    def test_comment(self):
        data = loads('# foo')
        eq_(len(data), 0)

    def test_multiline_comment(self):
        data = loads('# foo\n    bar\n    baz')
        eq_(len(data), 0)

    def test_blankline(self):
        data = loads('')
        eq_(len(data), 0)

    def test_blankline_with_space(self):
        data = loads(' ')
        eq_(len(data), 0)

    def test_broken(self):
        assert_raises(ValueError, loads, 'b0rked')


class TestDumpLoad:
    def dump_load(self, **data):
        s = dumps(data)
        restored = loads(s)
        eq_(len(data), len(restored))
        eq_(data.keys(), restored.keys())
        for key in data.keys():
            eq_(data[key], restored[key])

    def test_none(self):
        self.dump_load(nada=None)

    def test_oneline(self):
        self.dump_load(oneline='foo')

    def test_multiline(self):
        self.dump_load(multiline='foo\nbar\nbaz')

    def test_multivalue(self):
        self.dump_load(ans='1', zwo='2')
