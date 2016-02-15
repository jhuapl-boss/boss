from django.conf.urls import url
from bosscore import views

urlpatterns = [

    #Urls related to metadata
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)?/(?P<dataset>\w+)?/?$', views.BossMeta.as_view()),
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)?/?$', views.BossMeta.as_view()),
    url(r'(?P<collection>\w+)/$', views.BossMeta.as_view()),

]
