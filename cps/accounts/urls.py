from django.conf.urls import url
from accounts import views


urlpatterns = [
    url(r'^profile', views.view_profile, name='profile'),
    url(r'^password', views.change_password, name='change_password'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
]