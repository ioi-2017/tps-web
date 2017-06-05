from nose.tools import *

from git_orm.quote import quote_filename, unquote_filename


class TestQuote:
    def test_quote_unquote(self):
        testnames = [
            'foo',
            'foo\nbar',
            '!@#$%^&*()_+-[]\'\"|',
        ]
        for name in testnames:
            eq_(unquote_filename(quote_filename(name)), name)
