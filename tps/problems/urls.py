from django.conf import settings
from django.conf.urls import url

from .views import *


branch_mode_urls = [
    url(r'^merge_request/create/$', CreateMergeRequest.as_view(), name="create_merge_request"),
    url(r'^merge_request/list/$', MergeRequestList.as_view(), name="merge_requests_list"),
    url(r'^merge_request/(?P<merge_request_id>\d+)/$', MergeRequestDiscussionView.as_view(), name="merge_request"),
    url(r'^merge_request/(?P<merge_request_id>\d+)/$', MergeRequestDiscussionView.as_view(), name="merge_request_discussion"),
    url(r'^merge_request/(?P<merge_request_id>\d+)/changes/$', MergeRequestChangesView.as_view(), name="merge_request_changes"),
    url(r'^merge_request/(?P<merge_request_id>\d+)/reopen/$', MergeRequestReopenView.as_view(), name="merge_request_reopen"),
    url(r'^merge_request/(?P<merge_request_id>\d+)/follow/$', FollowMergeRequestView.as_view(), name="merge_request_follow"),
    url(r'^merge_request/(?P<merge_request_id>\d+)/unfollow/$', UnfollowMergeRequestView.as_view(), name="merge_request_unfollow"),
    url(r'^branch/list/$', BranchesListView.as_view(), name="branches_list"),
    url(r'^branch/create/$', CreateBranchView.as_view(), name="create_branch"),
    url(r'^delete/$', DeleteBranchView.as_view(), name="delete_branch"),
]

problem_urls = ([
        url(r'^analysis/$', AnalysisView.as_view(), name="analysis"),
        url(r'^analysis/generate/$', AnalysisGenerateView.as_view(), name="analysis_generate"),
        url(r'^analysis/analyze/$', AnalyzeView.as_view(), name="analyze"),

        url(r'^export/$', ExportView.as_view(), name="export"),
        url(r'export/(?P<export_id>\d+)/download/$', ExportDownloadView.as_view(), name="export_download"),
        url(r'export/(?P<export_id>\d+)/start/$', ExportPackageStarterView.as_view(), name="export_start"),

        url(r'statement/$', EditStatement.as_view(), name="statement"),
        url(r'statement/(?P<attachment_id>.+)$', DownloadStatementAttachment.as_view(), name="statement"),

        url(r'^history/$', HistoryView.as_view(), name="history"),
        url(r'^diff/(?P<other_slug>\w{1,40})/$', DiffView.as_view(), name="diff"),

        url(r'^$', Overview.as_view(), name="overview"),

        url(r'^discussions/$', DiscussionsListView.as_view(), name="discussions"),
        url(r'^discussion/add/$', DiscussionAddView.as_view(), name="add_discussion"),
        url(r'^discussion/(?P<discussion_id>\d+)/comments$', CommentListView.as_view(), name="comments"),

        url(r'^invocations/$', InvocationsListView.as_view(), name="invocations"),
        url(r'^invocation/add/$', InvocationAddView.as_view(), name="add_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/run/$', InvocationRunView.as_view(), name="run_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/clone/$', InvocationCloneView.as_view(), name="clone_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/view/$', InvocationDetailsView.as_view(), name="view_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/$', InvocationResultView.as_view(), name="view_invocation_result"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/download/output/$', InvocationOutputDownloadView.as_view(), name="download_output"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/download/input/$', InvocationInputDownloadView.as_view(), name="download_input"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/download/answer/$', InvocationAnswerDownloadView.as_view(), name="download_answer"),

        url(r'^resource/add/$', ResourceAddView.as_view(), name="add_resource"),
        url(r'^resource/(?P<resource_id>\d+)/edit/$', ResourceEditView.as_view(), name="edit_resource"),
        url(r'^resource/(?P<object_id>\d+)/delete/$', ResourceDeleteView.as_view(), name="delete_resource"),
        url(r'^resource/(?P<object_id>\d+)/download/$', ResourceDownloadView.as_view(), name="download_resource"),

        url(r'^solutions/$', SolutionsListView.as_view(), name="solutions"),
        url(r'^solution/add/$', SolutionAddView.as_view(), name="add_solution"),
        url(r'^solution/(?P<solution_id>.+)/edit/$', SolutionEditView.as_view(), name="edit_solution"),
        url(r'^solution/(?P<solution_id>.+)/delete/$', SolutionDeleteView, name="delete_solution"),
        url(r'^solution/(?P<solution_id>.+)/source/$', SolutionShowSourceView.as_view(), name="solution_source"),
        url(r'^solution/(?P<solution_id>.+)/download/$', SolutionDownloadView.as_view(), name="download_solution"),

        url(r'^graders/$', GradersListView.as_view(), name="graders"),
        url(r'^grader/add/$', GraderAddView.as_view(), name="add_grader"),
        url(r'^grader/(?P<grader_id>.+)/edit/$', GraderEditView.as_view(), name="edit_grader"),
        url(r'^grader/(?P<grader_id>.+)/delete/$', GraderDeleteView, name="delete_grader"),
        url(r'^grader/(?P<grader_id>.+)/source/$', GraderShowSourceView.as_view(), name="grader_source"),
        url(r'^grader/(?P<grader_id>.+)/download/$', GraderDownloadView.as_view(), name="download_grader"),


        url(r'^testcases/$', TestCasesListView.as_view(), name="testcases"),
        url(r'^testcase/add/$', TestCaseAddView.as_view(), name="add_testcase"),
        url(r'^testcase/(?P<testcase_id>.+)/edit/$', TestCaseEditView.as_view(), name="edit_testcase"),
        url(r'^testcase/(?P<testcase_id>.+)/delete/$', TestCaseDeleteView, name="delete_testcase"),
        url(r'^testcase/(?P<testcase_id>.+)/input/$', TestCaseInputDownloadView.as_view(), name="testcase_input"),
        url(r'^testcase/(?P<testcase_id>.+)/output/$', TestCaseOutputDownloadView.as_view(), name="testcase_output"),
        url(r'^testcase/(?P<testcase_id>.+)/generate/$', TestCaseGenerateView.as_view(), name="generate_testcase"),
        url(r'^testcase/generate/all/$', TestCaseGenerateView.as_view(), name="generate_testcase"),
        url(r'^testcase/(?P<testcase_id>.+)/details/$', TestCaseDetailsView.as_view(), name="testcase_details"),

        url(r'^subtasks/$', SubtasksListView.as_view(), name="subtasks"),
        url(r'^subtask/add/$', SubtaskAddView.as_view(), name="add_subtask"),
        url(r'^subtask/(?P<subtask_id>.+)/details/$', SubtaskDetailsView.as_view(), name="subtask_details"),
        url(r'^subtask/(?P<subtask_id>.+)/delete/$', SubtaskDeleteView, name="delete_subtask"),
        url(r'^subtask/(?P<subtask_id>.+)/edit/$', SubtaskEditView.as_view(), name="edit_subtask"),

        url(r'^validators/$', ValidatorsListView.as_view(), name="validators"),
        url(r'^validator/(?P<validator_id>.+)/edit/$', ValidatorEditView.as_view(), name="edit_validator"),
        url(r'^validator/(?P<validator_id>.+)/delete/$', ValidatorDeleteView, name="delete_validator"),
        url(r'^validator/(?P<validator_id>.+)/source/$', ValidatorShowSourceView.as_view(), name="validator_source"),
        url(r'^validator/add/$', ValidatorAddView.as_view(), name="add_validator"),
        url(r'^validator/(?P<validator_id>.+)/download/$', ValidatorDownloadView.as_view(), name="download_validator"),

        url(r'^generators/$', GeneratorsListView.as_view(), name="generators"),
        url(r'^generator/(?P<generator_id>.+)/edit/$', GeneratorEditView.as_view(), name="edit_generator"),
        url(r'^generator/(?P<generator_id>.+)/delete/$', GeneratorDeleteView, name="delete_generator"),
        url(r'^generator/(?P<generator_id>.+)/source/$', GeneratorShowSourceView.as_view(), name="generator_source"),
        url(r'^generator/add/$', GeneratorAddView.as_view(), name="add_generator"),
        url(r'^generator/(?P<generator_id>.+)/generate-testcases/$', GeneratorEnableView.as_view(),
            name="enable_generator"),
        url(r'^generator/(?P<generator_id>.+)/delete-testcases/$', GeneratorDisableView.as_view(),
            name="disable_generator"),

        url(r'^checkers/$', CheckerListView.as_view(), name="checkers"),
        url(r'^checker/add/$$', CheckerAddView.as_view(), name="add_checker"),
        url(r'^checker/(?P<checker_id>.+)/activate/$$', CheckerActivateView.as_view(), name="activate_checker"),
        url(r'^checker/(?P<checker_id>.+)/delete/$$', CheckerDeleteView, name="delete_checker"),
        url(r'^checker/(?P<checker_id>.+)/edit/$$', CheckerEditView.as_view(), name="edit_checker"),
        url(r'^checker/(?P<checker_id>.+)/source/$$', CheckerShowSourceView.as_view(), name="checker_source"),
        url(r'^checker/(?P<checker_id>.+)/download/$$', CheckerDownloadView.as_view(), name="download_checker"),

        url(r'^pull/$', PullBranchView.as_view(), name="pull_branch"),
        url(r'^commit/$', CommitWorkingCopy.as_view(), name="commit"),
        url(r'^discard/$', DiscardWorkingCopy.as_view(), name="discard"),
        url(r'^conflicts/$', ConflictsListView.as_view(), name="conflicts"),
        url(r'^conflict/(?P<conflict_id>\d+)/$', ResolveConflictView.as_view(), name="resolve_conflict"),

        url(r'files/list/$', ProblemFilesView.as_view(), name="files"),
        url(r'files/add/$', ProblemFileAddView.as_view(), name="add_file"),
        url(r'^files/(?P<file_id>\d+)/edit/$', ProblemFileEditView.as_view(), name="edit_file"),
        url(r'^files/(?P<file_id>\d+)/delete/$', ProblemFileDeleteView.as_view(), name="delete_file"),
        url(r'^files/(?P<file_id>\d+)/source/$', ProblemFileShowSourceView.as_view(), name="file_source"),
        url(r'^files/(?P<file_id>\d+)/download/$', ProblemFileDownloadView.as_view(), name="download_file"),
    ] + (branch_mode_urls if not settings.DISABLE_BRANCHES else []) , None, None)

urlpatterns = [
    url(r'^$', ProblemsListView.as_view(), name="problems"),
    url(r'^problem/(?P<problem_code>[^\/]+)/(?P<revision_slug>\w{1,40})/', problem_urls),
    url(r'^problem/add/$', ProblemAddView.as_view(), name="add_problem"),
]
