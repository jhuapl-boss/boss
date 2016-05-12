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
    # Specific coordinate frame
    url(r'coordinateframes/(?P<coordframe>[\w_-]+)/?$', views.CoordinateFrameDetail.as_view()),
    # All coordinate frames
    url(r'coordinateframes/?$', views.CoordinateFrameList.as_view()),

    # All channels for a experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/channels/?', views.ChannelList.as_view()),
    # All layers for a experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/layers/?', views.LayerList.as_view()),
    # An instance of a channel or layer
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/(?P<channel_layer>[\w_-]+)/?',
        views.ChannelLayerDetail.as_view()),

    # All experiments for a collection
    url(r'(?P<collection>[\w_-]+)/experiments/?', views.ExperimentList.as_view()),
    # An instance of an experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/?', views.ExperimentDetail.as_view()),

    # All collections
    url(r'collections/?$', views.CollectionList.as_view()),
    # An instance of a collection
    url(r'(?P<collection>[\w_-]+)/?$', views.CollectionDetail.as_view()),

]
