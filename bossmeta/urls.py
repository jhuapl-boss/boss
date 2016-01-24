from django.conf.urls import url
from bossmeta import views

urlpatterns = [

    url(r'^meta/collections/$', views.CollectionList.as_view()),
    url(r'^meta/experiments/$', views.ExperimentList.as_view()),
    url(r'^meta/datasets/$', views.DatasetList.as_view()),
    url(r'^meta/channels/$', views.ChannelList.as_view()),
    url(r'^meta/timesamples/$', views.TimeSampleList.as_view()),
    url(r'^meta/layers/$', views.LayerList.as_view()),
    url(r'^meta/coordinateframes/$', views.CoordinateFrameList.as_view()),


    url(r'^meta/(?P<col>.*)/(?P<exp>.*)/$', views.get_experiment),
    url(r'^meta/(?P<webargs>.*)/$', views.get_collection),


]
