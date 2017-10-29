from django import forms


class AutoFilledInput(forms.Widget):

    def render(self, name, value, attrs=None):
        return ""

    @property
    def is_hidden(self):
        return True
