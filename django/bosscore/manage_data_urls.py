# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls import url
from bosscore import views

urlpatterns = [
    # All channels for an experiment
    #url(r'(?P<collection>\w+)/(?P<experiment>\w+)/channels/?$', views.ChannelLayerObj.as_view()),
    # All layers for an experiment
    #url(r'(?P<collection>\w+)/(?P<experiment>\w+)/layers/?$', views.ChannelLayerObj.as_view()),
    # An instance of a channel or layer
    #url(r'(?P<collection>\w+)/(?P<experiment>\w+)/(?P<channel_layer>\w+)/?', views.ChannelLayerObj.as_view()),

    # Specific coordinate frame
    url(r'coordinateframes/(?P<coordframe>[\w_-]+)/?$', views.CoordinateFrameDetail.as_view()),
    # All coordinate frames
    url(r'coordinateframes/?$', views.CoordinateFrameList.as_view()),

    # All experiments for a collection
    url(r'(?P<collection>[\w_-]+)/experiments/?', views.ExperimentList.as_view()),
    # An instance of an experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/?', views.ExperimentDetail.as_view()),

    # All collections
    url(r'collections/?$', views.CollectionList.as_view()),
    # An instance of a collection
    url(r'(?P<collection>[\w_-]+)/?$', views.CollectionDetail.as_view()),


    # An instance of a collection
    #url(r'(?P<collection>[\w_-]+)/?$', views.CollectionDetail.as_view()),


]
