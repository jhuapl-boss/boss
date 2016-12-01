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
from __future__ import absolute_import

import os
import unittest
import json
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from bossingest.ingest_manager import IngestManager
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB

from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndqueue.ingestqueue import IngestQueue
from ndingest.ndingestproj.bossingestproj import BossIngestProj


class BossIntegrationIngestManagerTestMixin(object):

    def test_validate_ingest(self):
        """Method to test validation method"""

        # Validate schema and config file
        ingest_mgmr = IngestManager()
        response = ingest_mgmr.validate_config_file(self.example_config_data)
        assert (response is True)

        # Validate properties
        response = ingest_mgmr.validate_properties()
        assert (response is True)

    def test_validate_config_file(self):
        """Method to test validation of a config file"""
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        assert(ingest_mgmr.config is not None)
        assert (ingest_mgmr.config.config_data is not None)

    def test_validate_properties(self):
        """Methos to test validation of properties of the config data"""

        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        ingest_mgmr.validate_properties()
        assert (ingest_mgmr.collection.name == 'my_col_1')
        assert (ingest_mgmr.experiment.name == 'my_exp_1')
        assert (ingest_mgmr.channel.name == 'my_ch_1')

    def test_create_ingest_job(self):
        """Method to test creation o a ingest job from a config_data dict"""
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.id
        job = ingest_mgmr.create_ingest_job()
        assert (job.id is not None)

    def test_setup_ingest(self):
        """Method to test the setup_ingest method"""
        try:
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.setup_ingest(self.user.id, self.example_config_data)
            assert (ingest_job is not None)

            # Check if the queue's exist
            proj_class = BossIngestProj.load()
            nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                             ingest_job.resolution, ingest_job.id)
            ingest_mgmr.nd_proj = nd_proj
            upload_queue = UploadQueue(nd_proj, endpoint_url=None)
            assert(upload_queue is not None)
            ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
            assert (ingest_queue is not None)
            ingest_mgmr.remove_ingest_credentials(ingest_job.id)

        except:
            raise
        finally:
            ingest_mgmr.delete_upload_queue()
            ingest_mgmr.delete_ingest_queue()

    def test_generate_upload_tasks(self):
        """"""
        try:
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.setup_ingest(self.user.id, self.example_config_data)
            ingest_mgmr.generate_upload_tasks(ingest_job.id)
            assert (ingest_job.collection == 'my_col_1')
            assert (ingest_job.experiment == 'my_exp_1')
            assert (ingest_job.channel == 'my_ch_1')

            # Pull the messages off the queue
            proj_class = BossIngestProj.load()
            nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                             ingest_job.resolution, ingest_job.id)
            queue = UploadQueue(nd_proj, endpoint_url=None)

            tmp = queue.receiveMessage(number_of_messages=10)
            # receive message from the queue
            for message_id, receipt_handle, message_body in tmp:
                assert(message_body['job_id'] == ingest_job.id)

                # delete message from the queue
                response = queue.deleteMessage(message_id, receipt_handle)
                assert ('Successful' in response)
            ingest_mgmr.remove_ingest_credentials(ingest_job.id)

        except:
            raise
        finally:
            ingest_mgmr.delete_upload_queue()
            ingest_mgmr.delete_ingest_queue()


    @staticmethod
    def test_create_upload_task_message():
        """
        Test method that creates an upload task message
        Returns:

        """
        ingest_mgmr = IngestManager()
        msg = ingest_mgmr.create_upload_task_message(595, '3534561bd72dcfce1af7c041fc783379&16&1&1&1&0&1&1&3&0',
                                                     '3534561bd72dcfpppaf7c041fc783379&1&1&1&0&1&1&3&0',
                                                     'test_upload_queue_url', 'test_ingest_queue_url')
        msg = json.loads(msg)
        assert (msg['job_id'] == 595)


# class TestIntegrationBossIngestManager(BossIntegrationIngestManagerTestMixin, APITestCase):
    # TODO: Add test back after fixing ndingest
    # def setUp(self):
    #     # Get the config_data
    #     self.user = User.objects.create_superuser(username='testuser1', email='test@test.com', password='testuser')
    #     config_data = SetupTests().get_ingest_config_data_dict()
    #     self.example_config_data = config_data
    #     dbsetup = SetupTestDB()
    #     dbsetup.set_user(self.user)
    #     dbsetup.insert_ingest_test_data()


