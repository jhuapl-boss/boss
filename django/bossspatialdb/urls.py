from django.conf.urls import url
from . import views

urlpatterns = [
    # Url to handle cutout with a view
    url(r'^(?P<resolution>\d)/(?P<x_range>\d+:\d+)/(?P<y_range>\d+:\d+)/(?P<z_range>\d+:\d+)/?.*$',
        views.CutoutView.as_view()),
    # Url to handle cutout with a collection, experiment, dataset/annotation project
    url(r'^(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<resolution>\d)/(?P<x_range>\d+:\d+)/(?P<y_range>\d+:\d+)/(?P<z_range>\d+:\d+)/?.*$',
        views.Cutout.as_view()),
]
