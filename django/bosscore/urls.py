from django.conf.urls import url
from bosscore import views

urlpatterns = [
    # URLS related to the drf
    url(r'^info/collections/?$', views.CollectionList.as_view()),
    url(r'^info/experiments/?$', views.ExperimentList.as_view()),
    url(r'^info/datasets/?$', views.DatasetList.as_view()),
    url(r'^info/channels/?$', views.ChannelList.as_view()),
    url(r'^info/timesamples/?$', views.TimeSampleList.as_view()),
    url(r'^info/layers/?$', views.LayerList.as_view()),
    url(r'^info/coordinateframes/?$', views.CoordinateFrameList.as_view()),

    # Urls related to the data models
    url(r'^info/(?P<col>\w+)/(?P<exp>\w+)/(?P<ds>\w+)/(?P<channel>\w+)/(?P<ts>\w+)/(?P<layer>\w+)/?', views.layerObj),
    url(r'^info/(?P<col>\w+)/(?P<exp>\w+)/(?P<ds>\w+)/(?P<channel>\w+)/(?P<ts>\w+)/?', views.timesampleObj),
    url(r'^info/(?P<col>\w+)/(?P<exp>\w+)/(?P<ds>\w+)/(?P<channel>\w+)/?', views.channelObj),
    url(r'^info/(?P<col>\w+)/(?P<exp>\w+)/(?P<ds>\w+)/?', views.datasetObj),
    url(r'^info/(?P<col>\w+)/?$', views.collectionObj),
    url(r'^info/(?P<col>\w+)/(?P<exp>\w+)/?', views.experimentObj),

    # Urls related to metadata
    url(r'^meta/(?P<webargs>.*)/$$', views.boss_meta),
    url(r'^meta/(?P<col>\w+)/?(?P<exp>\w+)?/?(?P<ds>\w+)?/?(?P<channel>\w+)?/?(?P<ts>\w+)?/?(?P<layer>\w+)?/?$',
        views.boss_meta),
]
