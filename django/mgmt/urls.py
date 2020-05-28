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
from . import views

app_name = 'mgmt'
urlpatterns = [
    url(r'users/?', views.Users.as_view(), name='users'),
    url(r'user/(?P<username>[\w_-]+)/?', views.User.as_view(), name='user'),

    url(r'token/?', views.Token.as_view(), name='token'),

    url(r'groups/?', views.Groups.as_view(), name='groups'),
    url(r'group/(?P<group_name>[\w_-]+)/?', views.Group.as_view(), name='group'),

    url(r'resources/(?P<collection_name>[\w_-]+)/(?P<experiment_name>[\w_-]+)/(?P<channel_name>[\w_-]+)/?', views.Channel.as_view(), name='channel'),
    url(r'resources/(?P<collection_name>[\w_-]+)/(?P<experiment_name>[\w_-]+)/?', views.Experiment.as_view(), name='experiment'),
    url(r'resources/(?P<collection_name>[\w_-]+)/?', views.Collection.as_view(), name='collection'),
    url(r'resources/?', views.Resources.as_view(), name='resources'),

    url(r'coord/(?P<coord_name>[\w_-]+)/?', views.CoordinateFrame.as_view(), name='coord'),

    url(r'ingest/(?P<ingest_job_id>\d+)?/?', views.IngestJob.as_view(), name='ingest_job'),
    url(r'ingest/?', views.IngestJob.as_view(), name='ingest'),

    url(r'meta/(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/(?P<channel>[\w_-]+)/?', views.Meta.as_view(), name='meta'),
    url(r'meta/(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/?', views.Meta.as_view(), name='meta'),
    url(r'meta/(?P<collection>[\w_\-]+)/?$', views.Meta.as_view(), name='meta'),

    url(r'', views.Home.as_view(), name='home'),
]
