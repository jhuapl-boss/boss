from django.db import models


class Collection(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Collection")
    description = models.CharField(max_length=4096, blank=True)

    class Meta:
        db_table = u"collections"


class Experiment(models.Model):
    collection = models.ForeignKey(Collection, related_name='experiments')
    name = models.CharField(max_length=255, verbose_name="Name of the Experiment")
    description = models.CharField(max_length=4096, blank=True)
    num_resolution_levels = models.IntegerField(default=0)

    HIERARCHY_METHOD_CHOICES = (
        (0, 'near_iso'),
        (1, 'iso'),
        (2, 'slice'),
    )
    hierarchy_method = models.CharField(choices=HIERARCHY_METHOD_CHOICES, max_length=100)

    class Meta:
        db_table = u"experiments"

    def __unicode__(self):
        return '%s' % (self.name)


class CoordinateFrame(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Coordinate reference frame")
    description = models.CharField(max_length=4096, blank=True)

    x_extent = models.IntegerField()
    y_extent = models.IntegerField()
    z_extent = models.IntegerField()

    x_voxelsize = models.FloatField(default=1.0)
    y_voxelsize = models.FloatField(default=1.0)
    z_voxelsize = models.FloatField(default=1.0)

    class Meta:
        db_table = u"coordinate_frames"


class Dataset(models.Model):
    experiment = models.ForeignKey(Experiment, related_name='datasets')
    name = models.CharField(max_length=255, verbose_name="Name of the Dataset")
    description = models.CharField(max_length=4096, blank=True)

    IS_SOURCE_CHOICES = (
        (0, 'NO'),
        (1, 'YES'),
    )
    is_source = models.CharField(choices=IS_SOURCE_CHOICES, max_length=100)
    coord_frame = models.ForeignKey(CoordinateFrame, related_name='coord')

    default_channel = models.ForeignKey('Channel',related_name='default_channel', null = True)
    default_time = models.ForeignKey('TimeSample',related_name='default_time', null = True)
    default_layer = models.ForeignKey('Layer',related_name='default_layer',null = True)


    class Meta:
        db_table = u"datasets"

    def __unicode__(self):
        return '%s' % (self.dataset_name)


class Channel(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Channel")
    description = models.CharField(max_length=4096, blank=True)
    dataset = models.ForeignKey(Dataset, related_name='channels')

    class Meta:
        db_table = u"channels"


class TimeSample(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Time Sample ")
    description = models.CharField(max_length=4096, blank=True)
    channel = models.ForeignKey(Channel, related_name='timesamples')

    class Meta:
        db_table = u"time"


class Layer(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name of the Layer ")
    description = models.CharField(max_length=4096, blank=True)
    time = models.ForeignKey(TimeSample, related_name='layers')
    DATATYPE_CHOICES = (
        (0, 'uint8'),
        (1, 'uint16'),
        (2, 'uint32'),
        (3, 'uint64'),
    )

    datatype = models.CharField(choices=DATATYPE_CHOICES, max_length=100, blank = True)

    class Meta:
        db_table = u"layers"
