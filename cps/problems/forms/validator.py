from django import forms

from problems.models import SourceFile, Validator


class ValidatorAddForm(forms.ModelForm):
    class Meta:
        model = Validator
        fields = ["global_validator"]

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        super(ValidatorAddForm, self).__init__(*args, **kwargs)
        self.fields['sourcefile'] = forms.ModelChoiceField(
            queryset=SourceFile.objects.filter(problem=self.revision)
        )

    def save(self, commit=True):
        super(ValidatorAddForm, self).save(commit=False)
        self.instance.problem = self.revision
        self.instance.code = self.cleaned_data['sourcefile']
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
