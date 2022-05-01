from bootstrap3.renderers import FieldRenderer
from bootstrap3 import renderers
renderers.DBS3_SET_REQUIRED_SET_DISABLED = True


class ReadOnlyFieldRenderer(FieldRenderer):
    def __init__(self, *args, **kwargs):
        kwargs["set_disabled"] = True
        super(ReadOnlyFieldRenderer, self).__init__(*args, **kwargs)
