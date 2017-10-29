from django import forms

from problems.models import ExportPackage


class ExportForm(forms.ModelForm):
    class Meta:
        model = ExportPackage
        fields = ('exporter', 'export_format',)

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop('problem')
        self.revision = kwargs.pop('revision')
        self.creator = kwargs.pop('user')
        super(ExportForm, self).__init__(*args, **kwargs)

    def save(self, **kwargs):
        export_package = super(ExportForm, self).save(commit=False)
        export_package.problem = self.problem
        export_package.commit_id = self.revision.commit_id
        export_package.creator = self.creator
        export_package.save()
        return export_package
