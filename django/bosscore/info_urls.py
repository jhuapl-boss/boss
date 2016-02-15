from django.conf.urls import url
from bosscore import views

urlpatterns = [
    # URLS related to the django rest framework
    url(r'collections/?$', views.CollectionList.as_view()),
    url(r'experiments/?$', views.ExperimentList.as_view()),
    url(r'datasets/?$', views.DatasetList.as_view()),
    url(r'channels/?$', views.ChannelList.as_view()),
    url(r'timesamples/?$', views.TimeSampleList.as_view()),
    url(r'layers/?$', views.LayerList.as_view()),
    url(r'coordinateframes/?$', views.CoordinateFrameList.as_view()),

    # Urls related to the data models
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<channel>\w+)/(?P<timesample>\w+)/(?P<layer>\w+)/?', views.LayerObj.as_view()),
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<channel>\w+)/(?P<timesample>\w+)/?', views.TimesampleObj.as_view()),
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<channel>\w+)/?', views.ChannelObj.as_view()),
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/?', views.DatasetObj.as_view()),
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/?', views.ExperimentObj.as_view()),
    url(r'(?P<collection>\w+)/?$', views.CollectionObj.as_view()),


]
