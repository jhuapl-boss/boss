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

"""boss URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls import include

from . import views


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^ping/', views.Ping.as_view()),
    url(r'^token/', views.Token.as_view()),

    # API version 0.4
    url(r'^v0.4/meta/', include('bossmeta.urls', namespace='v0.4')),
    url(r'^v0.4/resource/', include('bosscore.urls.resource_urls', namespace='v0.4')),
    url(r'^v0.4/permission/', include('bosscore.urls.permission-urls', namespace='v0.4')),
    url(r'^v0.4/group/', include('bosscore.urls.group-urls', namespace='v0.4')),
    url(r'^v0.4/group-member/', include('bosscore.urls.group-urls', namespace='v0.4')),
    url(r'^v0.4/cutout/', include('bossspatialdb.urls', namespace='v0.4')),

    # API version 0.5
    url(r'^v0.5/meta/', include('bossmeta.urls', namespace='v0.5')),
    url(r'^v0.5/resource/', include('bosscore.urls.resource_urls', namespace='v0.5')),
    url(r'^v0.5/permission/', include('bosscore.urls.permission-urls', namespace='v0.5')),
    url(r'^v0.5/group/', include('bosscore.urls.group-urls', namespace='v0.5')),
    url(r'^v0.5/group-member/', include('bosscore.urls.group-member-urls', namespace='v0.5')),
    url(r'^v0.5/cutout/', include('bossspatialdb.urls', namespace='v0.5')),
    url(r'^v0.5/tiles/', include('bosstiles.urls', namespace='v0.5')),
    url(r'^v0.5/user/', include('bosscore.urls.user-urls', namespace='v0.5')),
    url(r'^v0.5/user-role/', include('bosscore.urls.user-role-urls', namespace='v0.5')),

]

if 'djangooidc' in settings.INSTALLED_APPS:
    urlpatterns.append(url(r'^openid/', include('djangooidc.urls')))
