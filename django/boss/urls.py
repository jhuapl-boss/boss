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
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^ping/', views.Ping.as_view()),
    url(r'^token/', views.Token.as_view()),

    # deprecated urls
    url(r'^v0.1/', views.Unsupported.as_view()),
    url(r'^v0.2/', views.Unsupported.as_view()),
    url(r'^v0.3/', views.Unsupported.as_view()),
    url(r'^v0.4/', views.Unsupported.as_view()),
    url(r'^v0.5/', views.Unsupported.as_view()),
    url(r'^v0.6/', views.Unsupported.as_view()),
    url(r'^v0.7/', views.Unsupported.as_view()),
    url(r'^v0.8/', views.Unsupported.as_view()),

    # API version 1
    url(r'^v1/meta/', include('bossmeta.urls', namespace='v1')),
    url(r'^v1/permissions/?', include('bosscore.urls.permission-urls', namespace='v1')),
    url(r'^v1/groups/', include('bosscore.urls.group-urls', namespace='v1')),
    url(r'^v1/cutout/', include('bossspatialdb.urls', namespace='v1')),
    url(r'^v1/downsample/', include('bossspatialdb.urls_downsample', namespace='v1')),
    url(r'^v1/image/', include('bosstiles.image_urls', namespace='v1')),
    url(r'^v1/tile/', include('bosstiles.tile_urls', namespace='v1')),
    url(r'^v1/ingest/', include('bossingest.urls', namespace='v1')),
    url(r'^v1/collection/', include('bosscore.urls.resource_urls', namespace='v1')),
    url(r'^v1/coord/', include('bosscore.urls.coord_urls', namespace='v1')),

    # SSO Urls
    url(r'^v1/sso/user/', include('sso.urls.user-urls', namespace='v1')),
    url(r'^v1/sso/user-role/', include('sso.urls.user-role-urls', namespace='v1')),

    # Management Console Urls
    url(r'^v1/mgmt/', include('mgmt.urls', namespace='mgmt')),
    url(r'^/?$', RedirectView.as_view(pattern_name='mgmt:home')),

    #Object urls
    url(r'^v1/reserve/', include('bossobject.urls.reserve_urls', namespace='v1')),
    url(r'^v1/ids/', include('bossobject.urls.ids_urls', namespace='v1')),
    url(r'^v1/boundingbox/', include('bossobject.urls.boundingbox_urls', namespace='v1')),
]

if 'djangooidc' in settings.INSTALLED_APPS:
    urlpatterns.append(url(r'^openid/', include('djangooidc.urls')))
