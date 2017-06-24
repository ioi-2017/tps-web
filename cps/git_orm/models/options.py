from uuid import uuid4

from django.utils.text import camel_case_to_spaces

from git_orm.models.fields import TextField, CreatedAtField, UpdatedAtField

from django.db.models.options import Options as DjangoOptions


class Options(DjangoOptions):
    def __init__(self, meta, app_label=None):
        super(Options, self).__init__(meta, app_label)
        self.fields = []
        self.storage_name = None
        self.json_db_name = None
        self.has_custom_queryset = False

    def contribute_to_class(self, cls, name):
        setattr(cls, name, self)
        self.model = cls
        self.object_name = cls.__name__
        self.model_name = self.object_name.lower()
        self.verbose_name = camel_case_to_spaces(self.object_name)
        self.storage_name = cls.__name__.lower() + 's'
        self.original_attrs = {}

        if self.meta:
            if hasattr(self.meta, 'storage_name'):
                self.storage_name = self.meta.storage_name
            if hasattr(self.meta, 'json_db_name'):
                self.json_db_name = self.meta.json_db_name

    def add_field(self, field, virtual=False):
        self.fields.append(field)
        if not self.pk and field.primary_key:
            self.pk = field

    def get_field(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        raise KeyError(
            '{} has no field named {}'.format(self.model.__name__, name))

    @property
    def writable_fields(self):
        return [f for f in self.fields if f.attname]

    def _prepare(self):
        if not self.pk:
            id_field = TextField(
                primary_key=True, default=lambda: uuid4().hex)
            self.model.add_to_class('id', id_field)
            self.fields.insert(0, self.fields.pop())
        fieldnames = [f.name for f in self.fields]
        if not 'created_at' in fieldnames:
            self.model.add_to_class('created_at', CreatedAtField())
        if not 'updated_at' in fieldnames:
            self.model.add_to_class('updated_at', UpdatedAtField())
