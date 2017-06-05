import re
import textwrap

__all__ = ['dumps', 'loads']

SPLIT_ITEMS = re.compile(r'\n(?!\s)').split
MATCH_ITEM = re.compile(r'''
    (?P<key>\w+):       # key
    \s?
    (?P<value>.*?)$     # first line
    (?P<value2>.+)?     # optional continuation line(s)
    ''', re.MULTILINE | re.DOTALL | re.VERBOSE).match


def dumps(data, comments={}):
    s = ''
    for k, v in data.items():
        comment = comments.get(k, None)
        if comment:
            s += '# ' + '\n  '.join(comment.splitlines()) + '\n'
        value = v or ''
        s += '{}: {}\n'.format(k, value.replace('\n', '\n    '))
    return s


def loads(serialized):
    data = {}
    lineno = 0
    for item in SPLIT_ITEMS(serialized):
        if not item.startswith('#') and item.strip():
            m = MATCH_ITEM(item)
            if not m:
                raise ValueError('syntax error on line {}'.format(lineno + 1))
            value = m.group('value')
            value += textwrap.dedent(m.group('value2') or '')
            data[m.group('key')] = value or None
        lineno += item.count('\n') + 1
    return data
