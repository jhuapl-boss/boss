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

    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)

    # Ingest type constants.
    TILE_INGEST = 0
    VOLUMETRIC_INGEST = 1

    INGEST_TYPE_OPTIONS = (
            (TILE_INGEST, 'Tile'),
            (VOLUMETRIC_INGEST, 'Volumetric')
        )

    # Ingest status constants.
    PREPARING = 0
    UPLOADING = 1
    COMPLETE = 2
    DELETED = 3
    FAILED = 4
    COMPLETING = 5
    WAIT_ON_QUEUES = 6

    INGEST_STATUS_OPTIONS = (
            (PREPARING, 'Preparing'),
            (UPLOADING, 'Uploading'),
            (COMPLETE, 'Complete'),
            (DELETED, 'Deleted'),
            (FAILED, 'Failed'),
            (COMPLETING, 'Completing'),
            (WAIT_ON_QUEUES, 'Wait on queues')
        )

    ingest_type = models.IntegerField(choices=INGEST_TYPE_OPTIONS, default=TILE_INGEST)
    status = models.IntegerField(choices=INGEST_STATUS_OPTIONS, default=PREPARING)
    upload_queue = models.URLField(max_length=512, null=True)
    ingest_queue = models.URLField(max_length=512, null=True)
    step_function_arn = models.URLField(max_length=512, null=True, blank=True)
    config_data = models.TextField()

    collection = models.CharField(max_length=128)
    experiment = models.CharField(max_length=128)
    channel = models.CharField(max_length=128)

    # Store the id for all these in case the names are changed.
    collection_id = models.IntegerField(null=True)
    experiment_id = models.IntegerField(null=True)
    channel_id = models.IntegerField(null=True)

    resolution = models.IntegerField()
    x_start = models.IntegerField()
    y_start = models.IntegerField()
    z_start = models.IntegerField()
    t_start = models.IntegerField()
    x_stop = models.IntegerField()
    y_stop = models.IntegerField()
    z_stop = models.IntegerField()
    t_stop = models.IntegerField()

    # Also use tile_size_* columns for chunk size for volumetric ingests.
    tile_size_x = models.IntegerField()
    tile_size_y = models.IntegerField()
    tile_size_z = models.IntegerField()
    tile_size_t = models.IntegerField()

    # Total number of tiles for this ingest job
    tile_count = models.IntegerField(default=0)

    # This timestamp is first set when the ingest job status is set to
    # WAIT_ON_QUEUES.
    wait_on_queues_ts = models.DateTimeField(null=True)

    class Meta:
        db_table = u"ingest_job"

    def __str__(self):
        return "{}".format(self.id)

    @staticmethod
    def get_ingest_status_str(status):
        """
        Get the string representation of an ingest status.

        Args:
            status (int): One of the status constants.

        Returns:
            (str)
        """
        return IngestJob.INGEST_STATUS_OPTIONS[status][1]
