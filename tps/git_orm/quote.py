import re
from binascii import unhexlify


RESERVED_CHARS = '/\\|?*<>:+[]"\u0000%'


def quote_filename(name):
    quoted = ''
    for c in name:
        if c in RESERVED_CHARS:
            for byte in c.encode('utf-8'):
                quoted += '%{:02x}'.format(byte)
        else:
            quoted += c
    return quoted


def unquote_filename(name):
    def _replace(m):
        return unhexlify(
            m.group(0).replace('%', '').encode('ascii')).decode('utf-8')
    return re.sub(r'(%[\da-f]{2})+', _replace, name)
