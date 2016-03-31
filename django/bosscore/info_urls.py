"""
Copyright 2016 The Johns Hopkins University Applied Physics Laboratory

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

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
