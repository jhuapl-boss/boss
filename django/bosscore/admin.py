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
from guardian.admin import GuardedModelAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from .models import Collection, Experiment, Channel, CoordinateFrame, BossRole, BossLookup, Source, BossGroup


class CollectionAdmin(GuardedModelAdmin):
    model = Collection


class ExperimentAdmin(GuardedModelAdmin):
    model = Experiment


class ChannelAdmin(GuardedModelAdmin):
    model = Channel


class SourceAdmin(GuardedModelAdmin):
    model = Source


class CoordinateFrameAdmin(GuardedModelAdmin):
    model = CoordinateFrame


class BossRoleAdmin(GuardedModelAdmin):
    model = BossRole


class BossLookupAdmin(GuardedModelAdmin):
    model = BossLookup


class BossGroupInline(admin.StackedInline):
    model = BossGroup


class GroupAdmin(BaseGroupAdmin):
    inlines = (BossGroupInline, )

admin.site.register(Collection, CollectionAdmin)
admin.site.register(Experiment, ExperimentAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(CoordinateFrame, CoordinateFrameAdmin)
admin.site.register(BossRole, BossRoleAdmin)
admin.site.register(BossLookup, BossLookupAdmin)

# Re-register GroupAdmin
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
