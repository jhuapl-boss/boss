# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
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

from django.db import models
from django.contrib.auth.models import Group
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class ThrottleMetric(models.Model):
    METRIC_UNITS_BYTES = 'byte_count'
    METRIC_UNITS_VOXELS = 'voxel_count'
    METRIC_UNITS = (
        (METRIC_UNITS_BYTES,'Threshold in bytes'),
        (METRIC_UNITS_VOXELS,'Threshold in voxels')
    )
    METRIC_TYPE_EGRESS = 'egress'
    METRIC_TYPE_INGRESS = 'ingress'
    METRIC_TYPE_COMPUTE = 'compute'
    METRIC_TYPES = (
        (METRIC_TYPE_EGRESS,'Egress level'),
        (METRIC_TYPE_INGRESS,'Engress level'),
        (METRIC_TYPE_COMPUTE,'Computation level')
    )
    mtype = models.CharField(choices=METRIC_TYPES,max_length=20)
    units = models.CharField(choices=METRIC_UNITS, max_length=20)
    def_system_limit = models.BigIntegerField(default=-1)
    def_api_limit = models.BigIntegerField(default=-1)
    def_user_limit = models.BigIntegerField(default=-1)

class ThrottleThreshold(models.Model):
    name = models.CharField(max_length=255)
    metric = models.ForeignKey(ThrottleMetric, on_delete=models.CASCADE)
    limit = models.BigIntegerField(default=-1)

class ThrottleUsage(models.Model):
    threshold = models.OneToOneField(ThrottleThreshold, on_delete=models.CASCADE)
    value = models.BigIntegerField(default=0)

class NameValidator(RegexValidator):
    regex = "^[a-zA-Z0-9_-]*$"
    message = u'Invalid Name.'


class Collection(models.Model):
    """
    Object representing a Boss Collection
    """
    name = models.CharField(max_length=255, verbose_name="Name of the Collection",
                            validators=[NameValidator()], unique=True)
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='collections')
    to_be_deleted = models.DateTimeField(null=True, blank=True)

    # ToDo: replace with constants.
    DELETED_STATUS_CHOICES = (
        ('started', 'STARTED'),
        ('finished', 'FINISHED'),
        ('error', 'ERROR')
    )
    deleted_status = models.CharField(choices=DELETED_STATUS_CHOICES, max_length=100, null=True, blank=True)

    class Meta:
        db_table = u"collection"
        managed = True
        default_permissions = ()
        permissions = (

            ('read', 'Can view resource'),
            ('update', 'Can update resource'),
            ('delete', 'Can delete resource'),
            ('add', 'Can add resources '),
            ('assign_group', 'Can assign groups permissions for the resource'),
            ('remove_group', 'Can remove groups permissions for the resource'),

        )

    def __str__(self):
        return self.name


class CoordinateFrame(models.Model):
    """
    Coordinate Frame for Boss Experiments

    """
    name = models.CharField(max_length=255, verbose_name="Name of the Coordinate reference frame",
                            validators=[NameValidator()], unique=True)
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='coordinateframes')

    x_start = models.IntegerField()
    x_stop = models.IntegerField()
    y_start = models.IntegerField()
    y_stop = models.IntegerField()
    z_start = models.IntegerField()
    z_stop = models.IntegerField()

    x_voxel_size = models.FloatField()
    y_voxel_size = models.FloatField()
    z_voxel_size = models.FloatField()

    # ToDo: replace with constants.
    VOXEL_UNIT_CHOICES = (
        ('nanometers', 'NANOMETERS'),
        ('micrometers', 'MICROMETERS'),
        ('millimeters', 'MILLIMETERS'),
        ('centimeters', 'CENTIMETERS')
    )
    voxel_unit = models.CharField(choices=VOXEL_UNIT_CHOICES, max_length=100)
    # time_step = models.IntegerField(blank=True, null=True)
    # TIMESTEP_UNIT_CHOICES = (
    #     ('nanoseconds', 'NANOSECONDS'),
    #     ('microseconds', 'MICROSECONDS'),
    #     ('milliseconds', 'MILLISECONDS'),
    #     ('seconds', 'SECONDS'),
    # )
    # time_step_unit = models.CharField(choices=TIMESTEP_UNIT_CHOICES, max_length=100, blank=True, null=True)
    to_be_deleted = models.DateTimeField(null=True, blank=True)
    # ToDo: replace with constants.
    DELETED_STATUS_CHOICES = (
        ('started', 'STARTED'),
        ('finished', 'FINISHED'),
        ('error', 'ERROR')
    )
    deleted_status = models.CharField(choices=DELETED_STATUS_CHOICES, max_length=100, null=True, blank=True)

    class Meta:
        db_table = u"coordinate_frame"

        default_permissions = ()
        permissions = (

            ('read', 'Can view resource'),
            ('update', 'Can update resource'),
            ('delete', 'Can delete resource'),
            ('add', 'Can add resources '),
            ('assign_group', 'Can assign groups permissions for the resource'),
            ('remove_group', 'Can remove groups permissions for the resource'),


        )

    def __str__(self):
        return self.name


class Experiment(models.Model):
    """
    Object representing a BOSS experiment
    """
    collection = models.ForeignKey(Collection, related_name='experiments', on_delete=models.PROTECT)
    name = models.CharField(max_length=255, verbose_name="Name of the Experiment", validators=[NameValidator()])
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='experiment')

    coord_frame = models.ForeignKey(CoordinateFrame, related_name='exps', on_delete=models.PROTECT)
    num_hierarchy_levels = models.IntegerField(default=1)

    # ToDo: replace with constants.
    HIERARCHY_METHOD_CHOICES = (
        ('anisotropic', 'ANISOTROPIC'),
        ('isotropic', 'ISOTROPIC'),
    )
    hierarchy_method = models.CharField(choices=HIERARCHY_METHOD_CHOICES, max_length=100, default='anisotropic')
    num_time_samples = models.IntegerField(default=1)
    time_step = models.IntegerField(blank=True, null=True)
    # ToDo: replace with constants.
    TIMESTEP_UNIT_CHOICES = (
        ('nanoseconds', 'NANOSECONDS'),
        ('microseconds', 'MICROSECONDS'),
        ('milliseconds', 'MILLISECONDS'),
        ('seconds', 'SECONDS'),
    )
    time_step_unit = models.CharField(choices=TIMESTEP_UNIT_CHOICES, max_length=100, blank=True, null=True)
    to_be_deleted = models.DateTimeField(null=True, blank=True)
    # ToDo: replace with constants.
    DELETED_STATUS_CHOICES = (
        ('started', 'STARTED'),
        ('finished', 'FINISHED'),
        ('error', 'ERROR')
    )
    deleted_status = models.CharField(choices=DELETED_STATUS_CHOICES, max_length=100, null=True, blank=True)

    class Meta:
        db_table = u"experiment"
        unique_together = ('collection', 'name')
        default_permissions = ()
        permissions = (

            ('read', 'Can view resource'),
            ('update', 'Can update resource'),
            ('delete', 'Can delete resource'),
            ('add', 'Can add resources '),
            ('assign_group', 'Can assign groups permissions for the resource'),
            ('remove_group', 'Can remove groups permissions for the resource'),
        )

    def __str__(self):
        return self.name


class Channel(models.Model):
    """
    Object representing a channel
    """
    name = models.CharField(max_length=255, verbose_name="Name of the Channel", validators=[NameValidator()])
    description = models.CharField(max_length=4096, blank=True)
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='Channel')

    experiment = models.ForeignKey(Experiment, related_name='channels', on_delete=models.PROTECT)
    base_resolution = models.IntegerField(default=0)
    default_time_sample = models.IntegerField(default=0)

    TYPE_CHOICES = (
        ('image', 'IMAGE'),
        ('annotation', 'ANNOTATION'),
    )
    type = models.CharField(choices=TYPE_CHOICES, max_length=100)

    # ToDo: replace with constants.
    DATATYPE_CHOICES = (
        ('uint8', 'UINT8'),
        ('uint16', 'UINT16'),
        ('uint32', 'UINT32'),
        ('uint64', 'UINT64'),
    )
    datatype = models.CharField(choices=DATATYPE_CHOICES, max_length=100)
    sources = models.ManyToManyField('self', through='Source', symmetrical=False, related_name='derived', blank=True)
    related = models.ManyToManyField('self', related_name='related', blank=True)
    to_be_deleted = models.DateTimeField(null=True, blank=True)
    # ToDo: replace with constants.
    DELETED_STATUS_CHOICES = (
        ('started', 'STARTED'),
        ('finished', 'FINISHED'),
        ('error', 'ERROR')
    )
    deleted_status = models.CharField(choices=DELETED_STATUS_CHOICES, max_length=100, null=True, blank=True)

    class DownsampleStatus:
        """
        String values are actual values stored in DB.

        This class is duplicated in boss-tools.git/activities/resolution_hierarchy.py.

        ToDo: consider making a separate shared repo with constants that the
        Django repo, step functions, and lambdas can all import.
        """
        NOT_DOWNSAMPLED = 'NOT_DOWNSAMPLED'
        IN_PROGRESS = 'IN_PROGRESS'
        DOWNSAMPLED = 'DOWNSAMPLED'
        FAILED = 'FAILED'
        QUEUED = 'QUEUED'

    DOWNSAMPLE_STATUS_CHOICES = (
        (DownsampleStatus.NOT_DOWNSAMPLED, 'Not Downsampled'),
        (DownsampleStatus.QUEUED, 'In Queue'),
        (DownsampleStatus.IN_PROGRESS, 'In Progress'),
        (DownsampleStatus.DOWNSAMPLED, 'Downsampled'),
        (DownsampleStatus.FAILED, 'Failed'),
    )
    downsample_status = models.CharField(choices=DOWNSAMPLE_STATUS_CHOICES, default=DownsampleStatus.NOT_DOWNSAMPLED, max_length=100)
    downsample_arn = models.CharField(max_length=4096, blank=True, null=True)

    class Meta:
        db_table = u"channel"
        unique_together = ('experiment', 'name')
        default_permissions = ()
        permissions = (
            ('read', 'Can view resource'),
            ('update', 'Can update resource'),
            ('delete', 'Can delete resource'),
            ('add', 'Can add resources '),
            ('assign_group', 'Can assign groups permissions for the resource'),
            ('remove_group', 'Can remove groups permissions for the resource'),
            ('add_volumetric_data', 'Can add volumetric data for the channel'),
            ('read_volumetric_data', 'Can read volumetric data for the channel'),
            ('delete_volumetric_data', 'Can delete volumetric data for the channel'),
        )

    def add_source(self, source):
        source, created = Source.objects.get_or_create(
            derived_channel=self,
            source_channel=source)
        return source

    def remove_source(self, source):
        Source.objects.filter(
            derived_channel=self,
            source_channel=source).delete()
        return

    def get_derived(self):
        """
        Get channels that list this channel as either a source or related channel.

        Do not return any channels that are marked for deletion.

        Returns:
            (QuerySet)
        """
        derived = Source.objects.filter(source_channel=self).exclude(derived_channel__to_be_deleted__isnull=False)
        return derived

    def __str__(self):
        return self.name


class Source(models.Model):
    derived_channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='derived_channel')
    source_channel = models.ForeignKey(Channel, related_name='source_channel', on_delete=models.PROTECT)


class BossLookup(models.Model):
    """
    Keeps track of the bosskey and maps it to a unique lookup key

    """
    lookup_key = models.CharField(max_length=255)
    boss_key = models.CharField(max_length=255)

    collection_name = models.CharField(max_length=255)
    experiment_name = models.CharField(max_length=255, blank=True, null=True)
    channel_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = u"lookup"
        unique_together = ('lookup_key', 'boss_key')

    def __str__(self):
        return 'Lookup key = {}, Boss key = {}'.format(self.lookup_key, self.boss_key)


class BossRole(models.Model):
    """
    Map user's to roles.
    """
    user = models.ForeignKey('auth.User', related_name='Role', on_delete=models.CASCADE)
    # ToDo: replace with constants.
    DATATYPE_CHOICES = (
        ('admin', 'ADMIN'),
        ('user-manager', 'USER-MANAGER'),
        ('resource-manager', 'RESOURCE-MANAGER'),
    )

    role = models.CharField(choices=DATATYPE_CHOICES, max_length=100)

    class Meta:
        db_table = u"role"
        unique_together = ('user', 'role')

    def __str__(self):
        return 'user = {}, role = {}'.format(self.user, self.role)


class BossGroup(models.Model):
    """
    Store group information
    """
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    creator = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='Bossgroup')

    class Meta:
        db_table = u"bossgroup"
        default_permissions = ()
        permissions = (
            ('maintain_group', 'Can add and remove people from the group'),
        )

    # @receiver(post_save, sender=Group)
    # def create_boss_group(sender, instance, created, **kwargs):
    #     if created:
    #         BossGroup.objects.create(group=instance)

    def create_boss_group(sender, **kwargs):
        BossGroup.objects.create(group=sender, creator=kwargs['creator'])
