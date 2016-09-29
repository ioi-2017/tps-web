from django import forms

from problems.forms.generic import ProblemObjectModelForm
from problems.models import Discussion, Comment


class DiscussionAddForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Discussion
        fields = ["title", "priority"]

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        self.owner = kwargs.pop("owner")
        super(DiscussionAddForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(DiscussionAddForm, self).save(commit=False)
        self.instance.author = self.owner
        self.instance.problem = self.problem
        self.instance.save()
        comment = Comment(discussion=self.instance, author=self.owner, text=self.cleaned_data["text"])
        comment.save()
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance


class CommentAddForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]

    def __init__(self, *args, **kwargs):
        self.discussion = kwargs.pop("discussion")
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        self.owner = kwargs.pop("owner")
        super(CommentAddForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        super(CommentAddForm, self).save(commit=False)
        self.instance.author = self.owner
        self.instance.discussion = self.discussion
        if commit:
            self.instance.save()
            self.save_m2m()
        return self.instance
