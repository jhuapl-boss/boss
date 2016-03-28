from django.db import models


class Collection(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Collection")
    description = models.CharField(max_length=4096, blank=True)

    class Meta:
        db_table = u"collection"


class CoordinateFrame(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Coordinate reference frame")
    description = models.CharField(max_length=4096, blank=True)

    x_start = models.IntegerField()
    x_stop = models.IntegerField()
    y_start = models.IntegerField()
    y_stop = models.IntegerField()
    z_start = models.IntegerField()
    z_stop = models.IntegerField()

    x_voxel_size = models.FloatField(default=1.0)
    y_voxel_size = models.FloatField(default=1.0)
    z_voxel_size = models.FloatField(default=1.0)

    VOXEL_UNIT_CHOICES = (
        ('nanometer', 'NANOMETER'),
        ('micrometer', 'MICROMETER'),
        ('millimeter', 'MILLIMETER'),
        ('centimeter', 'CENTIMETER')
    )
    voxel_unit = models.CharField(choices=VOXEL_UNIT_CHOICES, max_length=100)
    time_step = models.IntegerField()
    TIMESTEP_UNIT_CHOICES = (
        ('nanosecond', 'NANOSECOND'),
        ('microsecond', 'MICROSECOND'),
        ('millisecond', 'Millisecond'),
        ('centimeters', 'Centimeters'),
    )
    time_step_unit = models.CharField(choices=TIMESTEP_UNIT_CHOICES, max_length=100)

    class Meta:
        db_table = u"coordinate_frame"


class Experiment(models.Model):
    collection = models.ForeignKey(Collection, related_name='experiments')
    name = models.CharField(max_length=255, verbose_name="Name of the Experiment")
    description = models.CharField(max_length=4096, blank=True)
    coord_frame = models.ForeignKey(CoordinateFrame, related_name='coord')
    num_hierarchy_levels = models.IntegerField(default=0)

    HIERARCHY_METHOD_CHOICES = (
        ('near_iso', 'NEAR_ISO'),
        ('iso', 'ISO'),
        ('slice', 'SLICE'),
    )
    hierarchy_method = models.CharField(choices=HIERARCHY_METHOD_CHOICES, max_length=100)

    class Meta:
        db_table = u"experiment"

    def __unicode__(self):
        return '%s' % self.name


class ChannelLayer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Channel")
    description = models.CharField(max_length=4096, blank=True)
    experiment = models.ForeignKey(Experiment, related_name='channellayer')
    is_channel = models.BooleanField()
    base_resolution = models.IntegerField(default=0)
    default_time_step = models.IntegerField()
    DATATYPE_CHOICES = (
        ('unit8', 'UINT8'),
        ('uint16', 'UINT16'),
        ('uint32', 'UINT32'),
        ('uint62', 'UINT64'),
    )

    datatype = models.CharField(choices=DATATYPE_CHOICES, max_length=100, blank=True)
    max_time_step = models.IntegerField(default=0)
    layer_map = models.ManyToManyField('self', through='ChannelLayerMap', symmetrical=False)

    class Meta:
        db_table = u"channel_layer"


class ChannelLayerMap(models.Model):
    channel = models.ForeignKey(ChannelLayer, related_name='channel')
    layer = models.ForeignKey(ChannelLayer, related_name='layer')

    class Meta:
        db_table = u"channel_layer_map"
