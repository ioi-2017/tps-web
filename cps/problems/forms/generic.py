from django import forms


class ProblemObjectModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        self.owner = kwargs.pop("owner")
        super(ProblemObjectModelForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(ProblemObjectModelForm, self).save(commit=False)
        self.instance.problem = self.revision
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
