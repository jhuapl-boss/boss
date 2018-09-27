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
from unittest.mock import patch, MagicMock

from bossingest.ingest_manager import IngestManager, query_tile_index
from bossingest.models import IngestJob
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from bosscore.lookup import LookUpKey
import bossutils.aws
from django.contrib.auth.models import User
from ndingest.ndqueue.uploadqueue import UploadQueue
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

        setup = SetupTests()

        # Get the config_data for v1 schema
        config_data = setup.get_ingest_config_data_dict()
        self.example_config_data = config_data

        self.volumetric_config_data = setup.get_ingest_config_data_dict_volumetric()

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
        assert (job.ingest_type == IngestJob.TILE_INGEST)
        assert (job.tile_size_x == 512)
        assert (job.tile_size_y == 512)
        assert (job.tile_size_z == 1)
        assert (job.tile_size_t == 1)

    def test_create_ingest_job_volumetric(self):
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.volumetric_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.pk
        job = ingest_mgmr.create_ingest_job()
        assert (job.id is not None)
        assert (job.ingest_type == IngestJob.VOLUMETRIC_INGEST)
        assert (job.tile_size_x == 1024)
        assert (job.tile_size_y == 1024)
        assert (job.tile_size_z == 64)
        assert (job.tile_size_t == 1)

    def test_generate_upload_queue_args_tile_job(self):
        """Ensure ingest_type set properly"""
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.pk
        job = ingest_mgmr.create_ingest_job()
        actual = ingest_mgmr._generate_upload_queue_args(job)
        assert actual['ingest_type'] == IngestJob.TILE_INGEST
        assert actual['z_chunk_size'] == 16

    def test_generate_upload_queue_args_volumetric_job(self):
        """Ensure ingest_type set properly"""
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.volumetric_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.pk
        job = ingest_mgmr.create_ingest_job()
        actual = ingest_mgmr._generate_upload_queue_args(job)
        assert actual['ingest_type'] == IngestJob.VOLUMETRIC_INGEST
        assert actual['z_chunk_size'] == 64
        assert actual['ingest_queue'] is None

    def test_tile_bucket_name(self):
        """ Test get tile bucket name"""

        ingest_mgmr = IngestManager()
        tile_bucket_name = ingest_mgmr.get_tile_bucket()
        assert(tile_bucket_name is not None)

    @patch('bossutils.aws.get_region', return_value='us-east-1')
    @patch('bossingest.ingest_manager.query_tile_index', return_value=None)
    def test_verify_ingest_job_good(self, fake_query_tile_ind, fake_get_region):
        """Test with no chunks left in tile index"""
        ingest_mgmr = IngestManager()
        ingest_job = IngestJob()
        ingest_job.status = IngestJob.UPLOADING

        with patch.object(ingest_job, 'save') as fake_save:
            actual = ingest_mgmr.verify_ingest_job(ingest_job)
        self.assertTrue(actual)

    @patch('bossutils.aws.get_region', return_value='us-east-1')
    @patch('bossingest.ingest_manager.LookUpKey')
    @patch('bossingest.ingest_manager.UploadQueue')
    @patch('bossingest.ingest_manager.patch_upload_queue')
    @patch('bossingest.ingest_manager.query_tile_index', return_value='chunks.csv')
    def test_verify_ingest_job_not_ready(
        self, fake_query_tile_ind, fake_patch_upl_q, fake_upload_q, fake_lookup_key, fake_get_region
    ):
        """Test false returned when chunks still remain in tile index"""
        ingest_mgmr = IngestManager()
        ingest_job = IngestJob()
        ingest_job.status = IngestJob.UPLOADING
        ingest_job.collection = 'test_coll'
        ingest_job.experiment = 'test_exp'
        ingest_job.channel = 'test_chan'
        ingest_job.resolution = 0
        ingest_job.id = 8

        queue = MagicMock(spec=UploadQueue)
        queue.queue = MagicMock()
        fake_upload_q.return_value = queue
        key = MagicMock()
        key.lookup_key = '3&8&1'
        fake_lookup_key.get_lookup_key.return_value = key

        # Method under test.
        actual = ingest_mgmr.verify_ingest_job(ingest_job)

        self.assertFalse(actual)
        self.assertEqual(IngestJob.UPLOADING, ingest_job.status)
