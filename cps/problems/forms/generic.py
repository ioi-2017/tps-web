from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import construct_instance, InlineForeignKeyField


class ProblemObjectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        self.owner = kwargs.pop("owner")
        super(ProblemObjectForm, self).__init__(*args, **kwargs)


class ProblemObjectModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        self.owner = kwargs.pop("owner")
        super(ProblemObjectModelForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ProblemObjectModelForm, self).clean()
        cleaned_data["problem"] = self.revision
        return cleaned_data

    def _get_validation_exclusions(self):
        exclude = super(ProblemObjectModelForm, self)._get_validation_exclusions()
        exclude.remove("problem")
        return exclude

    def _post_clean(self):
        opts = self._meta

        exclude = self._get_validation_exclusions()

        try:
            self.instance = construct_instance(self, self.instance, opts.fields, exclude)
        except ValidationError as e:
            self._update_errors(e)

        self.instance.problem = self.cleaned_data["problem"]

        # Foreign Keys being used to represent inline relationships
        # are excluded from basic field value validation. This is for two
        # reasons: firstly, the value may not be supplied (#12507; the
        # case of providing new values to the admin); secondly the
        # object being referred to may not yet fully exist (#12749).
        # However, these fields *must* be included in uniqueness checks,
        # so this can't be part of _get_validation_exclusions().
        for name, field in self.fields.items():
            if isinstance(field, InlineForeignKeyField):
                exclude.append(name)

        try:
            self.instance.full_clean(exclude=exclude, validate_unique=False)
        except ValidationError as e:
            self._update_errors(e)

        # Validate uniqueness if needed.
        if self._validate_unique:
            self.validate_unique()

    def save(self, commit=True):
        super(ProblemObjectModelForm, self).save(commit=False)
        self.instance.problem = self.cleaned_data["problem"]
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
