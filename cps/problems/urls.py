from django.conf.urls import url

from problems.views.checker import CheckerChooseView
from problems.views.files import SourceFileCompileView
from problems.views.problems import ProblemAddView
from problems.views.validator import ValidatorsListView, ValidatorEditView, ValidatorDeleteView, ValidatorAddView
from .views import *




problem_urls = ([
        url(r'^$', Overview.as_view(), name="overview"),
        url(r'^discussions/$', DiscussionsListView.as_view(), name="discussions"),
        url(r'^files/$', FilesListView.as_view(), name="files"),
        url(r'^sourcefile/(?P<object_id>\d+)/delete/$', SourceFileDeleteView, name="delete_sourcefile"),
        url(r'^sourcefile/add/$', SourceFileAddView.as_view(), name="add_sourcefile"),
        url(r'^sourcefile/(?P<object_id>\d+)/delete/$', AttachmentDeleteView, name="delete_attachment"),
        url(r'^attachment/add/$', AttachmentAddView.as_view(), name="add_attachment"),
        url(r'^solutions/$', SolutionsListView.as_view(), name="solutions"),
        url(r'^solutions/add/$', SolutionAddView.as_view(), name="add_solution"),
        url(r'^solutions/(?P<solution_id>\d+)/edit/$', SolutionEditView.as_view(), name="edit_solution"),
        url(r'^solutions/(?P<solution_id>\d+)/delete/$', SolutionDeleteView, name="delete_solution"),
        url(r'^sourcefile/(?P<object_id>\d+)/compile/$', SourceFileCompileView.as_view(), name="compile_sourcefile"),
        url(r'^validators/$', ValidatorsListView.as_view(), name="validators"),
        url(r'^validators/(?P<validator_id>\d+)/edit/$', ValidatorEditView.as_view(), name="edit_validator"),
        url(r'^validators/(?P<validator_id>\d+)/delete/$', ValidatorDeleteView, name="delete_validator"),
        url(r'^validators/add/$', ValidatorAddView.as_view(), name="add_validator"),
        url(r'^checker/$', CheckerChooseView.as_view(), name="checker"),
        ], None, None)

urlpatterns = [
    url(r'^$', ProblemsListView.as_view(), name="problems"),
    url(r'^problem/(?P<problem_id>\d+)/', problem_urls),
    url(r'^problem/(?P<problem_id>\d+)/revision/(?P<revision_id>\d+)/', problem_urls),
    url(r'^problem/add/$', ProblemAddView.as_view(), name="add_problem"),
]