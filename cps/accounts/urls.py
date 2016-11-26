from django.conf.urls import url
from accounts import views


urlpatterns = [
    url(r'^profile', views.profile),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
]