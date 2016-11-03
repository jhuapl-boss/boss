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

    # # An instance of channel
    url(r'(?P<collection>[\w_-]+)/experiment/(?P<experiment>[\w_-]+)/channel/(?P<channel>[\w_-]+)/?',
        views_resource.ChannelDetail.as_view()),
    # All channels
    url(r'(?P<collection>[\w_-]+)/experiment/(?P<experiment>[\w_-]+)/channel/?',
        views_resource.ChannelList.as_view()),

    # An instance of an experiment
    url(r'(?P<collection>[\w_-]+)/experiment/(?P<experiment>[\w_-]+)/?',
        views_resource.ExperimentDetail.as_view()),
    # All experiments for a collection
    url(r'(?P<collection>[\w_-]+)/experiment/?', views_resource.ExperimentList.as_view()),

    # An instance of a collection
    url(r'(?P<collection>[\w-]+)/?', views_resource.CollectionDetail.as_view()),
    # All collections
    url(r'^', views_resource.CollectionList.as_view()),

]
