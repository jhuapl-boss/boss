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
from django.conf import settings

class IngestJob(models.Model):
    """
    Django Model representing an ingest job
    """

    creator = models.ForeignKey(settings.AUTH_USER_MODEL)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    INGEST_STATUS_OPTIONS = (
            (0, 'Preparing'),
            (1, 'Uploading'),
            (2, 'Complete'),
            (3, 'Deleted'),
        )
    status = models.IntegerField(choices=INGEST_STATUS_OPTIONS, default=0)
    upload_queue = models.URLField(max_length=512, null=True)
    ingest_queue = models.URLField(max_length=512, null=True)
    config_data = models.TextField()

    collection = models.CharField(max_length=128)
    experiment = models.CharField(max_length=128)
    channel_layer = models.CharField(max_length=128)

    resolution = models.IntegerField()
    x_start = models.IntegerField()
    y_start = models.IntegerField()
    z_start = models.IntegerField()
    t_start = models.IntegerField()
    x_stop = models.IntegerField()
    y_stop = models.IntegerField()
    z_stop = models.IntegerField()
    t_stop = models.IntegerField()

    tile_size_x = models.IntegerField()
    tile_size_y = models.IntegerField()
    tile_size_z = models.IntegerField()
    tile_size_t = models.IntegerField()

    class Meta:
        db_table = u"ingest_job"

    def __str__(self):
        return "{}".format(self.id)
