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
from bosscore.views import views_resource

urlpatterns = [
    # Specific coordinate frame
    url(r'coordinateframes/(?P<coordframe>[\w_-]+)/?$', views_resource.CoordinateFrameDetail.as_view()),
    # All coordinate frames
    url(r'coordinateframes/?$', views_resource.CoordinateFrameList.as_view()),

    # All channels for a experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/channels/?', views_resource.ChannelList.as_view()),
    # All layers for a experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/layers/?', views_resource.LayerList.as_view()),
    # An instance of a channel or layer
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/(?P<channel_layer>[\w_-]+)/?',
        views_resource.ChannelLayerDetail.as_view()),

    # All experiments for a collection
    url(r'(?P<collection>[\w_-]+)/experiments/?', views_resource.ExperimentList.as_view()),
    # An instance of an experiment
    url(r'(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/?', views_resource.ExperimentDetail.as_view()),

    # All collections
    url(r'collections/?$', views_resource.CollectionList.as_view()),
    # An instance of a collection
    url(r'(?P<collection>[\w_-]+)/?$', views_resource.CollectionDetail.as_view()),

]
