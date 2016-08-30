from django.conf.urls import url
from accounts import views

urlpatterns = [
    url(r'^profile', views.profile),
]