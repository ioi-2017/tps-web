from bootstrap3.renderers import FieldRenderer


class ReadOnlyFieldRenderer(FieldRenderer):
    def __init__(self, *args, **kwargs):
        kwargs["set_disabled"] = True
        super(ReadOnlyFieldRenderer, self).__init__(*args, **kwargs)