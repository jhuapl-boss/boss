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

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls import include
from django.conf import settings

from . import views

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

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls import include

from . import views


urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls',namespace='rest_framework')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^ping/', views.Ping.as_view()),
    url(r'^token/', views.Token.as_view()),

    # API version 0.3
    url(r'^v0.3/cutout/', include('bossspatialdb.urls', namespace='v0.3')),
    url(r'^v0.3/info/', include('bosscore.info_urls', namespace='v0.3')),
    url(r'^v0.3/meta/', include('bosscore.meta_urls', namespace='v0.3')),

    # API version 0.4
    url(r'^v0.4/meta/', include('bosscore.meta_urls', namespace='v0.4')),
    url(r'^v0.4/manage-data/', include('bosscore.manage_data_urls', namespace='v0.4')),
    url(r'^v0.4/cutout/', include('bossspatialdb.urls', namespace='v0.4')),

]

if 'djangooidc' in settings.INSTALLED_APPS:
    urlpatterns.append(url(r'^openid/', include('djangooidc.urls')))
