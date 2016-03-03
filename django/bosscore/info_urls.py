from django.conf.urls import url
from bosscore import views

urlpatterns = [
    # URLS related to the django rest framework
    url(r'collections/?$', views.CollectionList.as_view()),
    url(r'experiments/?$', views.ExperimentList.as_view()),
    url(r'channels/?$', views.ChannelList.as_view()),
    url(r'layers/?$', views.LayerList.as_view()),
    url(r'coordinateframes/?$', views.CoordinateFrameList.as_view()),

    # Urls related to the data models
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/(?P<channel_layer>\w+)/?', views.ChannelLayerObj.as_view()),
    url(r'(?P<collection>\w+)/(?P<experiment>\w+)/?', views.ExperimentObj.as_view()),
    url(r'(?P<collection>\w+)/?$', views.CollectionObj.as_view()),

]
