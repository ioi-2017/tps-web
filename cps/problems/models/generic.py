import json

import logging
from collections import OrderedDict

from git_orm import GitError
from git_orm.models import Model as GitModel

logger = logging.getLogger(__name__)


class JSONModel(GitModel):

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        model = cls
        if model._meta.json_db_name is not None:
            try:
                raw_data = transaction.get_blob([model._meta.json_db_name]).decode('utf-8')
                pks = json.loads(raw_data).keys()
            except GitError:
                logger.warning("{} not found".format(model._meta.json_db_name))
                pks = list()
            except (ValueError, UnicodeError) as e:
                raise model.InvalidObject(e)
        else:
            raise ValueError("json_db_name should be set in model's meta")

        return pks

    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = cls(pk=pk)
        obj._transaction = transaction
        try:
            raw_data = transaction.get_blob(obj.path).decode('utf-8')
            content = json.loads(raw_data)[pk]
        except KeyError:
            raise cls.DoesNotExist(
                'object with pk {} does not exist'.format(pk))
        except ValueError as e:
            raise cls.InvalidObject(e)

        obj.load(content)
        return obj

    def dump(self, include_hidden=False, include_pk=True):
        data = OrderedDict()
        for field in self._meta.writable_fields:
            if field.name == self._meta.pk.name and not include_pk:
                continue
            if field.hidden and not include_hidden:
                continue
            value = getattr(self, field.attname)
            data[field.name] = field.get_prep_value(value)
        return data

    @property
    def path(self):
        return [self._meta.json_db_name, ]

    def save(self):
        trans = self._transaction
        obj_dict = self.dump(include_hidden=True, include_pk=False)
        raw_data = trans.get_blob(self.path).decode('utf-8')
        content = json.loads(raw_data)
        content[self.pk] = obj_dict
        serialized = json.dumps(content)
        trans.set_blob(self.path, serialized.encode('utf-8'))
        # TODO: create informative commit message
        trans.add_message('Edit {}'.format(self))


class RecursiveDirectoryModel(GitModel):

    @classmethod
    def _get_existing_primary_keys(cls, transaction):
        return transaction.list_blobs([cls._meta.storage_name], recursive=True)


class ManuallyPopulatedModel(GitModel):
    @classmethod
    def _get_instance(cls, transaction, pk):
        obj = cls(pk=pk)
        obj._transaction = transaction
        obj.load(None)
        return obj

    def load(self, *args, **kwargs):
        return
