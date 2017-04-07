from __future__ import absolute_import

import json
import logging

from json import JSONDecoder
from json import JSONEncoder

from django.db import models


logger = logging.getLogger(__name__)


class DjangoPKJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, models.Model):
            return {
                'django_pk_encoded': True,
                'app_label': o._meta.app_label,
                'model_name': o._meta.model_name,
                'pk': o.pk,
            }
        return super(DjangoPKJSONEncoder, self).default(o)


class DjangoPKJSONDecoder(JSONDecoder):
    def __init__(self, object_hook=None, *args, **kwargs):
        if not object_hook:
            object_hook = self.pk_object_hook
        super(DjangoPKJSONDecoder, self).__init__(object_hook, *args, **kwargs)

    @staticmethod
    def pk_object_hook(json_dict):
        if 'django_pk_encoded' in json_dict:
            from django.apps import apps
            model = apps.get_model(json_dict['app_label'], json_dict['model_name'])
            return model.objects.get(pk=json_dict['pk'])
        else:
            return json_dict


class DjangoPKSerializer(object):

    name = 'django_pk_serializer'

    @staticmethod
    def model_encode(data):
        return json.dumps(data, cls=DjangoPKJSONEncoder)

    @staticmethod
    def model_decode(data):
        return json.loads(data, cls=DjangoPKJSONDecoder)

    @classmethod
    def register(cls):
        from kombu.serialization import register
        register(cls.name, cls.model_encode, cls.model_decode, 'application/json', 'utf-8')

