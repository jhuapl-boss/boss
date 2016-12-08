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
import json
from unittest.mock import patch

from bossingest.ingest_manager import IngestManager
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class BossIngestManagerTest(APITestCase):

    def setUp(self):
        """
            Initialize the database
            :return:
        """
        self.user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(self.user)

        self.client.force_login(self.user)
        dbsetup.insert_ingest_test_data()

        # Get the config_data
        config_data = SetupTests().get_ingest_config_data_dict()
        self.example_config_data = config_data

    def test_validate_ingest(self):
        """Method to test validation method"""
        #Validate schema and config file
        ingest_mgmr = IngestManager()
        response = ingest_mgmr.validate_config_file(self.example_config_data)
        assert (response is True)

        #Validate properties
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
        ingest_mgmr.owner = self.user.pk
        job = ingest_mgmr.create_ingest_job()
        assert (job.id is not None)


    def test_create_upload_task_message(self):
        """Test method that creates an upload task message"""

        ingest_mgmr = IngestManager()
        msg = ingest_mgmr.create_upload_task_message(595, '3534561bd72dcfce1af7c041fc783379&16&1&1&1&0&1&1&3&0',
                                                     '3534561bd72dcfpppaf7c041fc783379&1&1&1&0&1&1&3&0',
                                                     'test_upload_queue_url', 'test_ingest_queue_url')
        msg = json.loads(msg)
        assert (msg['job_id'] == 595)

    def test_tile_bucket_name(self):
        """ Test get tile bucket name"""

        ingest_mgmr = IngestManager()
        tile_bucket_name = ingest_mgmr.get_tile_bucket()
        assert(tile_bucket_name is not None)


    def test_create_ingest_credentials(self):
        """"""
        ingest_mgmr = IngestManager()
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.pk
        job = ingest_mgmr.create_ingest_job()
        ingest_mgmr.job = job
#        ingest_mgmr.create_ingest_credentials()


    def test_generate_upload_tasks(self):
        """
        Test that the correct number of messages are being uploaded
        """
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.pk
        job = ingest_mgmr.create_ingest_job()
        ingest_mgmr.job = job
        with patch.object(IngestManager, 'upload_task_file') as mock_method:
            ingest_mgmr.generate_upload_tasks(job.id)
            self.assertEquals(ingest_mgmr.file_index, 1)
            self.assertEquals(ingest_mgmr.num_of_chunks, 48)
            self.assertEquals(ingest_mgmr.count_of_tiles, 640)
