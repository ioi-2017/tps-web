from problems.forms.files import SourceFileAddForm, SourceFileEditForm
from problems.models import InputGenerator


class GeneratorAddForm(SourceFileAddForm):

    field_order = ['file', 'source_language', 'name', 'text_data']

    class Meta:
        model = InputGenerator
        fields = ["name", "source_language", "text_data"]



class GeneratorEditForm(SourceFileEditForm):

    field_order = ['file', 'source_language', 'name', 'text_data']

    class Meta:
        model = InputGenerator
        fields = ["name", "source_language", "text_data"]
