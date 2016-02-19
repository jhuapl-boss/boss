from django.conf.urls import patterns, include

urlpatterns = patterns('',
                       (r'^v0.2/info/', include('bosscore.info_urls')),
                       (r'^v0.2/meta/', include('bosscore.meta_urls')))
