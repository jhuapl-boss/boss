from django.db import models
from django.core.validators import RegexValidator

class NameValidator(RegexValidator):
    regex = "^[a-zA-Z0-9_-]*$"
    message = u'Invalid Name.'


class Collection(models.Model):
    """
    Object representing a Boss Collection
    """
    name = models.CharField(max_length=255, verbose_name="Name of the Collection",validators=[NameValidator()])
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', related_name='collections')

    class Meta:
        db_table = u"collection"
        managed = True
        permissions = (

            ('view_collection', 'Can view collection'),

        )

    def __str__(self):
        return self.name


class CoordinateFrame(models.Model):
    """
    Coordinate Frame for Boss Experiments

    """
    name = models.CharField(max_length=255, verbose_name="Name of the Coordinate reference frame",validators=[NameValidator()])
    description = models.CharField(max_length=4096, blank=True)
    #creator = models.ForeignKey('auth.User', related_name='coordinateframes')

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
        ('nanometers', 'NANOMETERS'),
        ('micrometers', 'MICROMETERS'),
        ('millimeters', 'MILLIMETERS'),
        ('centimeters', 'CENTIMETERS')
    )
    voxel_unit = models.CharField(choices=VOXEL_UNIT_CHOICES, max_length=100)
    time_step = models.IntegerField()
    TIMESTEP_UNIT_CHOICES = (
        ('nanoseconds', 'NANOSECONDS'),
        ('microseconds', 'MICROSECONDS'),
        ('milliseconds', 'MILLISECONDS'),
        ('seconds', 'SECONDS'),
    )
    time_step_unit = models.CharField(choices=TIMESTEP_UNIT_CHOICES, max_length=100)

    class Meta:
        db_table = u"coordinate_frame"

    def __str__(self):
        return self.name


class Experiment(models.Model):
    """
    Object representing a BOSS experiment
    """
    collection = models.ForeignKey(Collection, related_name='experiments')
    name = models.CharField(max_length=255, verbose_name="Name of the Experiment",validators=[NameValidator()])
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', related_name='experiment')

    coord_frame = models.ForeignKey(CoordinateFrame, related_name='coord')
    num_hierarchy_levels = models.IntegerField(default=0)

    HIERARCHY_METHOD_CHOICES = (
        ('near_iso', 'NEAR_ISO'),
        ('iso', 'ISO'),
        ('slice', 'SLICE'),
    )
    hierarchy_method = models.CharField(choices=HIERARCHY_METHOD_CHOICES, max_length=100)
    max_time_sample = models.IntegerField(default=0)

    class Meta:
        db_table = u"experiment"
        permissions = (
            ('view_experiment', 'Can view experiment'),
        )

    def __str__(self):
        return self.name


class ChannelLayer(models.Model):
    """
    Object representing a channel or layer. For image datasets these are channels and for annotations datasets these
    are layers.
    """
    name = models.CharField(max_length=255, verbose_name="Name of the Channel or Layer",validators=[NameValidator()])
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', related_name='ChannelLayer')

    experiment = models.ForeignKey(Experiment, related_name='channellayer')
    is_channel = models.BooleanField()
    base_resolution = models.IntegerField(default=0)
    default_time_step = models.IntegerField()
    DATATYPE_CHOICES = (
        ('uint8', 'UINT8'),
        ('uint16', 'UINT16'),
        ('uint32', 'UINT32'),
        ('uint64', 'UINT64'),
    )

    datatype = models.CharField(choices=DATATYPE_CHOICES, max_length=100, blank=True)

    # channels = models.ManyToManyField('self', through='ChannelLayerMap', symmetrical=False,
    # related_name='ref_channels')
    linked_channel_layers = models.ManyToManyField('self', through='ChannelLayerMap', symmetrical=False,
                                                   related_name='ref_layers_channels')

    class Meta:
        db_table = u"channel_layer"
        permissions = (
            ('view_channellayer', 'Can view channel or layer'),
        )

    def __str__(self):
        return self.name


class ChannelLayerMap(models.Model):
    """
    Many to many mapping betweens clannels and layers
    """
    channel = models.ForeignKey(ChannelLayer, related_name='channel')
    layer = models.ForeignKey(ChannelLayer, related_name='layer')

    class Meta:
        db_table = u"channel_layer_map"

    def __str__(self):
        return 'Channel = {}, Layer = {}'.format(self.channel.name, self.layer.name)


class BossLookup(models.Model):
    """
    Keeps track of the bosskey and maps it to a unique lookup key

    """
    lookup_key = models.CharField(max_length=255)
    boss_key = models.CharField(max_length=255)

    collection_name = models.CharField(max_length=255)
    experiment_name = models.CharField(max_length=255, blank=True, null=True)
    channel_layer_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = u"lookup"

    def __str__(self):
        return 'Lookup key = {}, Boss key = {}'.format(self.lookup_key,self. boss_key)