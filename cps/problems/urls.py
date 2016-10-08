from django.conf.urls import url

from problems.views.checker import CheckerChooseView
from problems.views.discussions import DiscussionAddView, CommentListView
from problems.views.files import SourceFileCompileView
from problems.views.invocations import InvocationAddView, InvocationsListView, InvocationRunView
from problems.views.problems import ProblemAddView
from problems.views.validator import ValidatorsListView, ValidatorEditView, ValidatorDeleteView, ValidatorAddView
from .views import *




problem_urls = ([
        url(r'^$', Overview.as_view(), name="overview"),
        url(r'^discussions/$', DiscussionsListView.as_view(), name="discussions"),
        url(r'^discussion/add/$', DiscussionAddView.as_view(), name="add_discussion"),
        url(r'^discussion/(?P<discussion_id>\d+)/comments$', CommentListView.as_view(), name="comments"),
        url(r'^files/$', FilesListView.as_view(), name="files"),
        url(r'^invocations/$', InvocationsListView.as_view(), name="invocations"),
        url(r'^invocation/add/$', InvocationAddView.as_view(), name="add_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/run/$', InvocationRunView.as_view(), name="run_invocation"),

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

        url(r'^clone/', CreateWorkingCopy.as_view(), name="create_working_copy"),
        url(r'^update/', UpdateForkView.as_view(), name="update_fork"),
        url(r'^commit/', CommitWorkingCopy.as_view(), name="commit"),
        url(r'^conflicts/', ConflictsListView.as_view(), name="conflicts"),
        url(r'^conflict/(?P<conflict_id>\d+)/', ResolveConflictView.as_view(), name="resolve_conflict"),
        url(r'^apply/', ApplyForkToMaster.as_view(), name="apply_fork"),

    ], None, None)

urlpatterns = [
    url(r'^$', ProblemsListView.as_view(), name="problems"),
    url(r'^problem/(?P<problem_id>\d+)/(?P<revision_slug>[0-9a-z]{1,40})/', problem_urls),
    url(r'^problem/add/$', ProblemAddView.as_view(), name="add_problem"),
]