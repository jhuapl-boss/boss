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

from django.contrib import admin
from .models import *
from guardian.admin import GuardedModelAdmin

class CollectionAdmin(GuardedModelAdmin):
    model = Collection


class ExperimentAdmin(GuardedModelAdmin):
    model = Experiment


class ChannelLayerAdmin(GuardedModelAdmin):
    model = ChannelLayer


class CoordinateFrameAdmin(GuardedModelAdmin):
    model = CoordinateFrame


class ChannelLayerMapAdmin(GuardedModelAdmin):
    model = ChannelLayerMap


admin.site.register(Collection,CollectionAdmin)
admin.site.register(Experiment,ExperimentAdmin)
admin.site.register(ChannelLayer,ChannelLayerAdmin)
admin.site.register(CoordinateFrame,CoordinateFrameAdmin)
admin.site.register(ChannelLayerMap,ChannelLayerMapAdmin)