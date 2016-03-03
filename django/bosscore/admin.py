from django.contrib import admin

from .models import *

admin.site.register(Collection)
admin.site.register(Experiment)
admin.site.register(ChannelLayer)
admin.site.register(CoordinateFrame)
