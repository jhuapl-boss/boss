from django.contrib import admin


from .models import Collection, Experiment, Dataset, Channel, TimeSample, Layer, CoordinateFrame

admin.site.register(Collection)
admin.site.register(Experiment)
admin.site.register(Dataset)
admin.site.register(Channel)
admin.site.register(TimeSample)
admin.site.register(Layer)
admin.site.register(CoordinateFrame)
