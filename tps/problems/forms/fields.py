from django import forms

from problems.forms.widgets import AutoFilledInput


class AutoFilledField(forms.Field):

    widget = AutoFilledInput

    def __init__(self, initial=None):
        super(AutoFilledField, self).__init__(initial=initial, required=False)

    def clean(self, value):
        return self.initial
