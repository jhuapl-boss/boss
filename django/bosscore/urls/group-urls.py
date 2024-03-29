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
from bosscore.views import views_group

app_name = 'bosscore'
urlpatterns = [

    # urls to manage adding and removing users from groups
    url(r'(?P<group_name>[\w_-]+)/maintainers/?(?P<user_name>[\w_-]+)?/?',views_group.BossGroupMaintainer.as_view()),

    # urls to manage adding and removing users from groups
    url(r'(?P<group_name>[\w_-]+)/members/?(?P<user_name>[\w_-]+)?/?',views_group.BossGroupMember.as_view()),


    # urls to manage creation and deletion of groups
    url(r'(?P<group_name>[\w_-]+)/?',views_group.BossUserGroup.as_view()),

    # URLS to manage groups
    url(r'^', views_group.BossUserGroup.as_view()),

]
