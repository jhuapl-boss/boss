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

from pkg_resources import resource_filename
import json
from django.contrib.auth.models import User

from bossutils.aws import get_region

import boto3
from moto import mock_sqs
from moto import mock_sqs
import time

from bossingest.models import IngestJob


class SetupTests(object):
    """ Class to handle setting up tests, including support for mocking

    """
    def __init__(self):
        self.mock_sqs = None

    def start_mocking(self):
        """Method to start mocking"""
        self.mock = True
        self.mock_sqs = mock_sqs()
        self.mock_sqs.start()

    def stop_mocking(self):
        """Method to stop mocking"""
        self.mock_sqs.stop()

    # ***** Upload Task SQS Queue *****
    def _create_upload_queue(self, queue_name):
        """Method to create a test sqs for uploading tiles for the ingest"""
        client = boto3.client('sqs', region_name=get_region())
        response = client.create_queue(QueueName=queue_name)
        url = response['QueueUrl']
        return url

    def create_upload_queue(self, queue_name):
        """Method to create a test sqs for uploading tiles for the ingest"""
        if self.mock:
            url = mock_sqs(self._create_upload_queue(queue_name))
        else:
            url = self._create_upload_queue(queue_name)
            time.sleep(30)
        return url

    def _delete_upload_queue(self, queue_url):
        """Method to delete a test sqs for uploading tiles for the ingest"""
        client = boto3.client('sqs', region_name=get_region())
        client.delete_queue(QueueUrl=queue_url)

    def delete_upload_queue(self, queue_name):
        """Method to delete a test sqs for uploading tiles for the ingest"""
        if self.mock:
            mock_sqs(self._delete_upload_queue(queue_name))
        else:
            self._delete_upload_queue(queue_name)
    # ***** END Flush SQS Queue *****

    def get_ingest_config_data_dict(self):
        """Method to get the config dictionary ingest job"""
        data = {}
        data['schema'] = {}
        data['schema']['name'] = "boss-v0.1-schema"
        data['schema']['validator'] = "BossValidatorV01"

        data['client'] = {}
        data['client']['backend'] = {}
        data['client']['backend']['name'] = "boss"
        data['client']['backend']['class'] = "BossBackend"
        data['client']['backend']['host'] = "api.theboss.io"
        data['client']['backend']['protocol'] = "https"

        data['client']['path_processor'] = {}
        data['client']['path_processor']['class'] = "ingest.plugins.multipage_tiff.SingleTimeTiffPathProcessor"
        data['client']['path_processor']['params'] = {}

        data['client']['tile_processor'] = {}
        data['client']['tile_processor']['class'] = "ingest.plugins.multipage_tiff.SingleTimeTiffTileProcessor"
        data['client']['tile_processor']['params'] = {}

        data['database'] = {}
        data['database']['collection'] = "my_col_1"
        data['database']['experiment'] = "my_exp_1"
        data['database']['channel'] = "my_ch_1"

        data['ingest_job'] = {}
        data['ingest_job']['resolution'] = 0
        data['ingest_job']['extent'] = {}
        data['ingest_job']['extent']['x'] = [0, 512]
        data['ingest_job']['extent']['y'] = [0, 1024]
        data['ingest_job']['extent']['z'] = [0, 2]
        data['ingest_job']['extent']['t'] = [0, 1]

        data['ingest_job']['tile_size'] = {}
        data['ingest_job']['tile_size']['x'] = 512
        data['ingest_job']['tile_size']['y'] = 512
        data['ingest_job']['tile_size']['z'] = 1
        data['ingest_job']['tile_size']['t'] = 1
        return data

    def create_ingest_job(self, creator = None):
        config_data = self.get_ingest_config_data_dict()
        # create the django model for the job
        if creator is None:
            user = User.objects.get(pk=1)
        else:
            user = creator

        ingest_job_data = {
            'creator': user,
            'collection': config_data["database"]["collection"],
            'experiment': config_data["database"]["experiment"],
            'channel': config_data["database"]["channel"],
            'resolution': 0,
            'config_data': config_data,
            'x_start': config_data["ingest_job"]["extent"]["x"][0],
            'x_stop': config_data["ingest_job"]["extent"]["x"][1],
            'y_start': config_data["ingest_job"]["extent"]["y"][0],
            'y_stop': config_data["ingest_job"]["extent"]["y"][1],
            'z_start': config_data["ingest_job"]["extent"]["z"][0],
            'z_stop': config_data["ingest_job"]["extent"]["z"][1],
            't_start': config_data["ingest_job"]["extent"]["t"][0],
            't_stop': config_data["ingest_job"]["extent"]["t"][1],
            'tile_size_x': config_data["ingest_job"]["tile_size"]["x"],
            'tile_size_y': config_data["ingest_job"]["tile_size"]["y"],
            'tile_size_z': config_data["ingest_job"]["tile_size"]["z"],
            'tile_size_t': config_data["ingest_job"]["tile_size"]["t"],
        }

        job = IngestJob.objects.create(**ingest_job_data)
        job.save()
        return job



