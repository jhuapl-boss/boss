from django.conf.urls import url
from django.conf.urls import patterns, include   

urlpatterns = patterns('',
                       (r'^v0.1/info/', include('bosscore.info_urls')),
                       (r'^v0.1/meta/', include('bosscore.meta_urls')))
