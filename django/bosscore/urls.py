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
    url(r'^info/(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<channel>\w+)/(?P<timesample>\w+)/(?P<layer>\w+)/?', views.LayerObj.as_view()),
    url(r'^info/(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<channel>\w+)/(?P<timesample>\w+)/?', views.TimesampleObj.as_view()),
    url(r'^info/(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<channel>\w+)/?', views.ChannelObj.as_view()),
    url(r'^info/(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/?', views.DatasetObj.as_view()),
    url(r'^info/(?P<collection>\w+)/(?P<experiment>\w+)/?', views.ExperimentObj.as_view()),
    url(r'^info/(?P<collection>\w+)/?$', views.CollectionObj.as_view()),

    # Urls related to metadata
   # url(r'^meta/(?P<webargs>.*)/$$', views.boss_meta),
   # url(r'^meta/(?P<collection>\w+)/?(?P<experiment>\w+)?/?(?P<dataset>\w+)?/?(?P<channel>\w+)?/?(?P<timesample>\w+)?/?(?P<layer>\w+)?/?$',views.boss_meta),

    #Urls related to metadata
    url(r'^meta/(?P<collection>\w+)/(?P<experiment>\w+)?/(?P<dataset>\w+)?/?$', views.BossMeta.as_view()),
    url(r'^meta/(?P<collection>\w+)/(?P<experiment>\w+)?/?$', views.BossMeta.as_view()),
    url(r'^meta/(?P<collection>\w+)/$', views.BossMeta.as_view()),
    

    #url(r'^meta/(?P<collection>\w+)/?(?P<experiment>\w+)?/?(?P<dataset>\w+)?/?(?P<channel>\w+)?/?(?P<timesample>\w+)?/?(?P<layer>\w+)?/?$',views.boss_meta),

]
