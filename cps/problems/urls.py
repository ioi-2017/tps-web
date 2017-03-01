from django.conf.urls import url


from .views import *

problem_urls = ([
        url(r'^export/$', ExportView.as_view(), name="export"),
        url(r'export/(?P<export_id>\d+)/download/$', ExportDownloadView.as_view(), name="export_download"),
        url(r'export/(?P<export_id>\d+)/start/$', ExportPackageStarterView.as_view(), name="export_start"),

        url(r'statement/$', EditStatement.as_view(), name="statement"),

        url(r'^history/$', HistoryView.as_view(), name="history"),
        url(r'^$', Overview.as_view(), name="overview"),
        url(r'^discussions/$', DiscussionsListView.as_view(), name="discussions"),
        url(r'^discussion/add/$', DiscussionAddView.as_view(), name="add_discussion"),
        url(r'^discussion/(?P<discussion_id>\d+)/comments$', CommentListView.as_view(), name="comments"),

        url(r'^invocations/$', InvocationsListView.as_view(), name="invocations"),
        url(r'^invocation/add/$', InvocationAddView.as_view(), name="add_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/run/$', InvocationRunView.as_view(), name="run_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/view/$', InvocationDetailsView.as_view(), name="view_invocation"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/$', InvocationResultView.as_view(), name="view_invocation_result"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/download/output/$', InvocationOutputDownloadView.as_view(), name="download_output"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/download/input/$', InvocationInputDownloadView.as_view(), name="download_input"),
        url(r'^invocation/(?P<invocation_id>\d+)/invocation_result/(?P<result_id>\d+)/view/download/answer/$', InvocationAnswerDownloadView.as_view(), name="download_answer"),

        url(r'^resource/add/$', ResourceAddView.as_view(), name="add_resource"),
        url(r'^resource/(?P<resource_id>\d+)/edit/$', ResourceEditView.as_view(), name="edit_resource"),
        url(r'^resource/(?P<object_id>\d+)/delete/$', ResourceDeleteView.as_view(), name="delete_resource"),

        url(r'^solutions/$', SolutionsListView.as_view(), name="solutions"),
        url(r'^solution/add/$', SolutionAddView.as_view(), name="add_solution"),
        url(r'^solution/(?P<solution_id>\d+)/edit/$', SolutionEditView.as_view(), name="edit_solution"),
        url(r'^solution/(?P<solution_id>\d+)/delete/$', SolutionDeleteView, name="delete_solution"),
        url(r'^solution/(?P<solution_id>\d+)/source/$', SolutionShowSourceView.as_view(), name="solution_source"),

        url(r'^graders/$', GradersListView.as_view(), name="graders"),
        url(r'^grader/add/$', GraderAddView.as_view(), name="add_grader"),
        url(r'^grader/(?P<grader_id>\d+)/edit/$', GraderEditView.as_view(), name="edit_grader"),
        url(r'^grader/(?P<grader_id>\d+)/delete/$', GraderDeleteView, name="delete_grader"),
        url(r'^grader/(?P<grader_id>\d+)/source/$', GraderShowSourceView.as_view(), name="grader_source"),

        url(r'^testcases/$', TestCasesListView.as_view(), name="testcases"),
        url(r'^testcase/add/$', TestCaseAddView.as_view(), name="add_testcase"),
        url(r'^testcase/(?P<testcase_id>\d+)/edit/$', TestCaseEditView.as_view(), name="edit_testcase"),
        url(r'^testcase/(?P<testcase_id>\d+)/delete/$', TestCaseDeleteView, name="delete_testcase"),
        url(r'^testcase/(?P<testcase_id>\d+)/input/$', TestCaseInputDownloadView.as_view(), name="testcase_input"),
        url(r'^testcase/(?P<testcase_id>\d+)/output/$', TestCaseOutputDownloadView.as_view(), name="testcase_output"),
        url(r'^testcase/(?P<testcase_id>\d+)/generate/$', TestCaseGenerateView.as_view(), name="generate_testcase"),
        url(r'^testcase/generate/all/$', TestCaseGenerateView.as_view(), name="generate_testcase"),
        url(r'^testcase/(?P<testcase_id>\d+)/details/$', TestCaseDetailsView.as_view(), name="testcase_details"),

        url(r'^subtasks/$', SubtasksListView.as_view(), name="subtasks"),
        url(r'^subtask/add/$', SubtaskAddView.as_view(), name="add_subtask"),
        url(r'^subtask/(?P<subtask_id>\d+)/details/$', SubtaskDetailsView.as_view(), name="subtask_details"),
        url(r'^subtask/(?P<subtask_id>\d+)/delete/$', SubtaskDeleteView, name="delete_subtask"),
        url(r'^subtask/(?P<subtask_id>\d+)/edit/$', SubtaskEditView.as_view(), name="edit_subtask"),

        url(r'^validators/$', ValidatorsListView.as_view(), name="validators"),
        url(r'^validator/(?P<validator_id>\d+)/edit/$', ValidatorEditView.as_view(), name="edit_validator"),
        url(r'^validator/(?P<validator_id>\d+)/delete/$', ValidatorDeleteView, name="delete_validator"),
        url(r'^validator/(?P<validator_id>\d+)/source/$', ValidatorShowSourceView.as_view(), name="validator_source"),
        url(r'^validator/add/$', ValidatorAddView.as_view(), name="add_validator"),

        url(r'^generators/$', GeneratorsListView.as_view(), name="generators"),
        url(r'^generator/(?P<generator_id>\d+)/edit/$', GeneratorEditView.as_view(), name="edit_generator"),
        url(r'^generator/(?P<generator_id>\d+)/delete/$', GeneratorDeleteView, name="delete_generator"),
        url(r'^generator/(?P<generator_id>\d+)/source/$', GeneratorShowSourceView.as_view(), name="generator_source"),
        url(r'^generator/add/$', GeneratorAddView.as_view(), name="add_generator"),
        url(r'^generator/(?P<generator_id>\d+)/generate-testcases/$', GeneratorEnableView.as_view(),
            name="enable_generator"),
        url(r'^generator/(?P<generator_id>\d+)/delete-testcases/$', GeneratorDisableView.as_view(),
            name="disable_generator"),

        url(r'^checkers/$', CheckerListView.as_view(), name="checkers"),
        url(r'^checker/add/$$', CheckerAddView.as_view(), name="add_checker"),
        url(r'^checker/(?P<checker_id>\d+)/activate/$$', CheckerActivateView.as_view(), name="activate_checker"),
        url(r'^checker/(?P<checker_id>\d+)/delete/$$', CheckerDeleteView, name="delete_checker"),
        url(r'^checker/(?P<checker_id>\d+)/edit/$$', CheckerEditView.as_view(), name="edit_checker"),
        url(r'^checker/(?P<checker_id>\d+)/source/$$', CheckerShowSourceView.as_view(), name="checker_source"),

        url(r'^clone/$', CreateWorkingCopy.as_view(), name="create_working_copy"),
        url(r'^pull/$', PullBranchView.as_view(), name="pull_branch"),
        url(r'^commit/$', CommitWorkingCopy.as_view(), name="commit"),
        url(r'^conflicts/$', ConflictsListView.as_view(), name="conflicts"),
        url(r'^conflict/(?P<conflict_id>\d+)/$', ResolveConflictView.as_view(), name="resolve_conflict"),
        url(r'^create_branch/$', CreateBranchView.as_view(), name="create_branch"),

        url(r'^merge_request/create/$', CreateMergeRequest.as_view(), name="create_merge_request"),
        url(r'^merge_request/list/$', MergeRequestList.as_view(), name="merge_requests_list"),
        url(r'^merge_request/(?P<merge_request_id>\d+)/$', MergeRequestDiscussionView.as_view(), name="merge_request"),
        url(r'^merge_request/(?P<merge_request_id>\d+)/$', MergeRequestDiscussionView.as_view(), name="merge_request_discussion"),
        url(r'^merge_request/(?P<merge_request_id>\d+)/changes/$', MergeRequestChangesView.as_view(), name="merge_request_changes"),
    ], None, None)

urlpatterns = [
    url(r'^$', ProblemsListView.as_view(), name="problems"),
    url(r'^problem/(?P<problem_id>\d+)/(?P<revision_slug>[0-9a-z]{1,40})/', problem_urls),
    url(r'^problem/add/$', ProblemAddView.as_view(), name="add_problem"),
]
