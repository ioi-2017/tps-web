from django.conf.urls import url

from .views import *

problem_urls = ([
        url(r'^discussions/$', DiscussionsListView.as_view(), name="discussions"),
        url(r'^files/$', FilesListView.as_view(), name="files"),
        url(r'^solutions/$', SolutionsListView.as_view(), name="solutions"),
        url(r'^solutions/add/$', SolutionAddView.as_view(), name="add_solution"),
        url(r'^solutions/(?P<solution_id>\d+)/edit/$', SolutionEditView.as_view(), name="edit_solution"),
        url(r'^solutions/(?P<solution_id>\d+)/delete/$', SolutionDeleteView.as_view(), name="delete_solution"),
    ], None, None)

urlpatterns = [
    url(r'^$', ProblemsListView.as_view(), name="problems"),
    url(r'^problem/(?P<problem_id>\d+)/', problem_urls),
    url(r'^problem/(?P<problem_id>\d+)/revision/(?P<revision_id>\d+)/', problem_urls),

]