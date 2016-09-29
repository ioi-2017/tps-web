from django.conf.urls import url

from problems.views.checker import CheckerChooseView
from problems.views.discussions import DiscussionAddView, CommentListView
from problems.views.files import SourceFileCompileView
from problems.views.problems import ProblemAddView
from problems.views.validator import ValidatorsListView, ValidatorEditView, ValidatorDeleteView, ValidatorAddView
from .views import *




problem_urls = ([
        url(r'^$', Overview.as_view(), name="overview"),
        url(r'^discussions/$', DiscussionsListView.as_view(), name="discussions"),
        url(r'^discussion/add/$', DiscussionAddView.as_view(), name="add_discussion"),
        url(r'^discussion/(?P<discussion_id>\d+)/comments$', CommentListView.as_view(), name="comments"),
        url(r'^files/$', FilesListView.as_view(), name="files"),
        
        url(r'^sourcefile/add/$', SourceFileAddView.as_view(), name="add_sourcefile"),
        url(r'^sourcefile/(?P<object_id>\d+)/delete/$', SourceFileDeleteView, name="delete_sourcefile"),
        url(r'^sourcefile/(?P<object_id>\d+)/compile/$', SourceFileCompileView.as_view(), name="compile_sourcefile"),
        
        url(r'^attachment/add/$', AttachmentAddView.as_view(), name="add_attachment"),
        url(r'^attachment/(?P<object_id>\d+)/delete/$', AttachmentDeleteView, name="delete_attachment"),
        
        url(r'^solutions/$', SolutionsListView.as_view(), name="solutions"),
        url(r'^solution/add/$', SolutionAddView.as_view(), name="add_solution"),
        url(r'^solution/(?P<solution_id>\d+)/edit/$', SolutionEditView.as_view(), name="edit_solution"),
        url(r'^solution/(?P<solution_id>\d+)/delete/$', SolutionDeleteView, name="delete_solution"),
        
        url(r'^testcases/$', TestCasesListView.as_view(), name="testcases"),
        url(r'^testcase/add/$', TestCaseAddView.as_view(), name="add_testcase"),
        url(r'^testcase/(?P<testcase_id>\d+)/input/$', TestCaseInputDownloadView.as_view(), name="download_testcase_input"),
        url(r'^testcase/(?P<testcase_id>\d+)/output/$', TestCaseOutputDownloadView.as_view(), name="download_testcase_output"),
        
        url(r'^validators/$', ValidatorsListView.as_view(), name="validators"),
        url(r'^validator/(?P<validator_id>\d+)/edit/$', ValidatorEditView.as_view(), name="edit_validator"),
        url(r'^validator/(?P<validator_id>\d+)/delete/$', ValidatorDeleteView, name="delete_validator"),
        url(r'^validator/add/$', ValidatorAddView.as_view(), name="add_validator"),
        
        url(r'^checker/$', CheckerChooseView.as_view(), name="checker"),

        url(r'^update/', MergeForksView.as_view(), name="update_working_copy"),
        url(r'^commit/', CommitWorkingCopy.as_view(), name="update_working_copy"),
    ], None, None)

urlpatterns = [
    url(r'^$', ProblemsListView.as_view(), name="problems"),
    url(r'^problem/(?P<problem_id>\d+)/(?P<revision_slug>[0-9a-z]{1,40})/', problem_urls),
    url(r'^problem/add/$', ProblemAddView.as_view(), name="add_problem"),
]