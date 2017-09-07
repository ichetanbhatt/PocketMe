from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^event$', views.event, name='event'),
    url(r'^auth$', views.auth, name='request_token'),
    url(r'^register$', views.slashcmd, name='slashcmd'),
    url(r'^response$', views.btn_response, name='response'),
    url(r'^redirect$', views.auth_redirect, name='redirect'),
    url(r'^db$', views.db, name='db'),

]