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