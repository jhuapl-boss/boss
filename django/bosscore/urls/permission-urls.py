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
from bosscore.views import views_permission

app_name = 'bosscore'
urlpatterns = [

    # URLS for permissions - Group to resource
    #url(r'(?P<group_name>[\w_-]+)/(?P<collection>[\w_-]+)/?(?P<experiment>[\w_-]+)?/?(?P<channel>[\w_-]+)?/?',
    #    views_permission.ResourceUserPermission.as_view()),

    url(r'^', views_permission.ResourceUserPermission.as_view()),


]
