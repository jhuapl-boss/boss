from django.db import models


class Collection(models.Model):

    collection_name = models.CharField(max_length = 255, primary_key = True,verbose_name = "Name of the Collection")
    collection_description = models.CharField(max_length = 4096,blank = True)

    class Meta:
        db_table= u"collections"



class Experiment(models.Model):

    collection = models.ForeignKey(Collection,related_name = 'experiments')
    experiment_name = models.CharField(max_length = 255, primary_key = True,verbose_name = "Name of the Experiment")
    experiment_description = models.CharField(max_length = 4096,blank = True)
    num_resolution_levels = models.IntegerField(default = 0)

    HEIRARCHY_METHOD_CHOICES = (
        (0, 'near_iso'),
        (1, 'iso'),
        (2, 'slice'),
    )
    heirarchy_method = models.CharField(choices = HEIRARCHY_METHOD_CHOICES, max_length = 100)

    class Meta:
        db_table = u"experiments"

    def __unicode__(self):
        return '%s' % (self.experiment_name)


class CoordinateFrame(models.Model):
    
    coord_name = models.CharField(max_length = 255, primary_key = True,verbose_name = "Name of the Coordinate reference frame")
    coord_description = models.CharField(max_length = 4096,blank = True)
    
    xextent =  models.IntegerField()
    yextent =  models.IntegerField()
    zextent =  models.IntegerField()

    xvoxelsize = models.FloatField(default = 1.0)
    yvoxelsize = models.FloatField(default = 1.0)
    zvoxelsize = models.FloatField(default = 1.0)

    class Meta:
        db_table = u"coordinate_frames"



class Dataset(models.Model):

    experiment = models.ForeignKey(Experiment,related_name ='datasets')
    dataset_name = models.CharField(max_length = 255, primary_key = True,verbose_name = "Name of the Dataset")
    dataset_description = models.CharField(max_length = 4096,blank = True)

    IS_SOURCE_CHOICES = (
        (0, 'NO'),
        (1, 'YES'),
    )
    is_source = models.CharField(choices = IS_SOURCE_CHOICES, max_length = 100)
    coord_frame = models.ForeignKey(CoordinateFrame,related_name ='coord')

   # default_channel = models.ForeignKey(Channel,related_name='default_channel')
   # default_time_sample = models.ForeignKey(Time_Sample,related_name='default_time_sample')
   # default_layer = models.ForeignKey(Layer,related_name='default_layer')

    
    DATATYPE_CHOICES = (
        (0, 'uint8'),
        (1, 'uint16'),
        (2, 'uint32'),
    )
    datatype = models.CharField(choices = DATATYPE_CHOICES, max_length = 100)

    class Meta:
        db_table = u"datasets"

    def __unicode__(self):
        return '%s' % (self.dataset_name)


class Channel(models.Model):

    channel_name = models.CharField(max_length = 255, primary_key = True, verbose_name = "Name of the Channel")
    channel_description = models.CharField(max_length = 4096, blank = True)
    dataset = models.ForeignKey(Dataset ,related_name = 'channels')

    class Meta:
        db_table = u"channels"

class TimeSample(models.Model):

    ts_name = models.CharField(max_length = 255, primary_key = True,verbose_name = "Name of the Time Sample ")
    ts_description = models.CharField(max_length=4096,blank=True)
    channel = models.ForeignKey(Channel,related_name = 'timesamples')

    class Meta:
        db_table = u"timesamples"

class Layer(models.Model):

    layer_name = models.CharField(max_length = 255, primary_key = True,verbose_name = "Name of the Layer ")
    layer_description = models.CharField(max_length = 4096,blank = True)
    timesample = models.ForeignKey(TimeSample,related_name = 'layers')

    class Meta:
        db_table = u"layers"
