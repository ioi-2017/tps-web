from enum import Enum

import six
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import TypedChoiceField
from django.utils.encoding import force_text


class EnumChoiceField(TypedChoiceField):
    def prepare_value(self, value):
        if value is None:
            return ''
        if isinstance(value, Enum):
            value = value.name
        return force_text(value)


class EnumField(models.CharField):
    def __init__(self, enum, **kwargs):
        self.enum = enum
        if "choices" not in kwargs:
            self.passed_choices = False
            choices = []
            for item in self.enum:
                choices.append((item, item))
            kwargs["choices"] = choices
        else:
            self.passed_choices = True

        if "default" in kwargs:
            kwargs["default"] = self.to_python(kwargs["default"])

        kwargs.setdefault("max_length", max(
            [len(i.name) for i in self.enum]
        ))

        super(EnumField, self).__init__(**kwargs)

        self.validators = self.validators[:-1]

    def to_python(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, self.enum):
            return value
        return self.enum.__members__.get(value)

    def get_prep_value(self, value):
        value = self.to_python(value)
        if value is None:
            return None
        return value.name

    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return None
        return self.to_python(value)

    def deconstruct(self):
        name, path, args, kwargs = super(EnumField, self).deconstruct()
        kwargs['enum'] = self.enum
        if not self.passed_choices:
            kwargs.pop("choices")
        if "default" in kwargs and isinstance(kwargs["default"], self.enum):
            kwargs["default"] = kwargs["default"].name
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        kwargs.setdefault("choices_form_class", EnumChoiceField)
        return super(EnumField, self).formfield(**kwargs)

    def get_choices(self, *args, **kwargs):
        return [(i.name if isinstance(i, self.enum) else i, _)
                for i, _ in super(EnumField, self).get_choices(*args, **kwargs)]



