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
from management import views

urlpatterns = [
    url(r'users/?', views.Users.as_view(), name='manage-users'),
    url(r'user/(?P<username>[\w_-]+)/?', views.User.as_view(), name='manage-user'),
    url(r'token/?', views.Token.as_view(), name='manage-token'),
    url(r'groups/?', views.Groups.as_view(), name='manage-groups'),
    url(r'group/(?P<group_name>[\w_-]+)/?', views.Group.as_view(), name='manage-group'),
    url(r'resources/?', views.Resources.as_view(), name='manage-resources'),
    url(r'collection/(?P<collection_name>[\w_-]+)/?', views.Collection.as_view(), name='manage-collection'),
    url(r'', views.Home.as_view(), name='manage-home'),
]
