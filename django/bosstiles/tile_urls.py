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
from bosstiles import views

urlpatterns = [
    # Url to handle cutout with a collection, experiment, dataset/annotation project
    url(r'^(?P<collection>[\w_-]+)/(?P<experiment>[\w_-]+)/(?P<dataset>[\w_-]+)/(?P<orientation>(xy|xz|yz))/(?P<tile_size>\d+)/(?P<resolution>\d)/(?P<x_idx>\d+)/(?P<y_idx>\d+)/(?P<z_idx>\d+)/?(?P<t_idx>\d+)?/?.*$',
        views.Tile.as_view()),
]
