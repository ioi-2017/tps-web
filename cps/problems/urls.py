from django.conf.urls import url

from problems.views.discussions import DiscussionsListView
from .views import ProblemsListView

urlpatterns = [
    url(r'^$', ProblemsListView.as_view()),
    url(r'^problem/(?P<problem_id>\d+)/', ([
        url(r'discussions/$', DiscussionsListView.as_view()),
    ], None, None)),
]