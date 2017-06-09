from uuid import uuid4

from git_orm.models.fields import TextField, CreatedAtField, UpdatedAtField

from django.db.models.options import Options as DjangoOptions


class Options(DjangoOptions):
    def __init__(self, meta):
        super(Options, self).__init__(meta)
        self.meta = meta
        self.fields = []
        self.pk = None
        self.storage_name = None

    def contribute_to_class(self, cls, name):
        setattr(cls, name, self)
        self.model = cls
        self.storage_name = cls.__name__.lower() + 's'

        if self.meta:
            if hasattr(self.meta, 'storage_name'):
                self.storage_name = self.meta.storage_name

    def add_field(self, field):
        self.fields.append(field)
        print("here @addfield", self, field, self.model.__name__)
        if not self.pk and field.primary_key:
            print("here pk set to ", field)
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
            print("fucked up", self.model.__name__)
            id_field = TextField(
                primary_key=True, hidden=True, default=lambda: uuid4().hex)
                # primary_key=True, default=lambda: uuid4().hex)
            self.model.add_to_class('id', id_field)
            self.fields.insert(0, self.fields.pop())
        fieldnames = [f.name for f in self.fields]
        if not 'created_at' in fieldnames:
            self.model.add_to_class('created_at', CreatedAtField())
        if not 'updated_at' in fieldnames:
            self.model.add_to_class('updated_at', UpdatedAtField())
