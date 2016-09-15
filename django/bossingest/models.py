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
from django.db import models


class IngestSchema(models.Model):
    """
    Object representing an Ingest Schema
    """
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=128)
    schema = models.TextField()
    deprecated = models.BooleanField(default=False)

    class Meta:
        unique_together = (("name", "version"),)

    def __str__(self):
        return "{}-v{}".format(self.name, self.version)


class IngestJob(models.Model):
    """
    Object representing an Ingest Job
    """
    STATUSES = (
        (0, 'Preparing'),
        (1, 'Uploading'),
        (2, 'Complete'),
    )

    status = models.IntegerField(choices=STATUSES, default=0)
    upload_queue = models.URLField(max_length=512)
    owner = models.CharField(max_length=512)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    config_data = models.TextField()
    collection = models.CharField(max_length=128)
    experiment = models.CharField(max_length=128)
    channel_layer = models.CharField(max_length=128)
    range_x_start = models.IntegerField()
    range_y_start = models.IntegerField()
    range_z_start = models.IntegerField()
    range_t_start = models.IntegerField()
    range_x_stop = models.IntegerField()
    range_y_stop = models.IntegerField()
    range_z_stop = models.IntegerField()
    range_t_stop = models.IntegerField()
    offset_x = models.IntegerField()
    offset_y = models.IntegerField()
    offset_z = models.IntegerField()
    offset_t = models.IntegerField()
    tile_size_x = models.IntegerField()
    tile_size_y = models.IntegerField()
    tile_size_z = models.IntegerField()
    tile_size_t = models.IntegerField()
    channel_list = models.CharField(max_length=512, null=True, blank=True)

    def __str__(self):
        return "{} - {}".format(self.channel_layer, self.status)
