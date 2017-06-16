import json

__all__ = ['dumps', 'loads']


def dumps(data, comments={}):
    return json.dumps(data)


def loads(serialized):
    return serialized
