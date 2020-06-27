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

import json
from unittest.mock import patch, MagicMock

from bossingest.ingest_manager import IngestManager
from bossingest.models import IngestJob
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from bosscore.error import ErrorCodes
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

        # Unit under test.
        self.ingest_mgr = IngestManager()

    def test_validate_ingest(self):
        """Method to test validation method"""
        #Validate schema and config file
        response = self.ingest_mgr.validate_config_file(self.example_config_data)
        assert (response is True)

        #Validate properties
        response = self.ingest_mgr.validate_properties()
        assert (response is True)

    def test_validate_config_file(self):
        """Method to test validation of a config file"""
        self.ingest_mgr.validate_config_file(self.example_config_data)
        assert(self.ingest_mgr.config is not None)
        assert (self.ingest_mgr.config.config_data is not None)

    def test_validate_properties(self):
        """Methos to test validation of properties of the config data"""
        self.ingest_mgr.validate_config_file(self.example_config_data)
        self.ingest_mgr.validate_properties()
        assert (self.ingest_mgr.collection.name == 'my_col_1')
        assert (self.ingest_mgr.experiment.name == 'my_exp_1')
        assert (self.ingest_mgr.channel.name == 'my_ch_1')

    def test_create_ingest_job(self):
        """Method to test creation o a ingest job from a config_data dict"""
        self.ingest_mgr.validate_config_file(self.example_config_data)
        self.ingest_mgr.validate_properties()
        self.ingest_mgr.owner = self.user.pk
        job = self.ingest_mgr.create_ingest_job()
        assert (job.id is not None)
        assert (job.ingest_type == IngestJob.TILE_INGEST)
        assert (job.tile_size_x == 512)
        assert (job.tile_size_y == 512)
        assert (job.tile_size_z == 1)
        assert (job.tile_size_t == 1)

    def test_create_ingest_job_volumetric(self):
        self.ingest_mgr.validate_config_file(self.volumetric_config_data)
        self.ingest_mgr.validate_properties()
        self.ingest_mgr.owner = self.user.pk
        job = self.ingest_mgr.create_ingest_job()
        assert (job.id is not None)
        assert (job.ingest_type == IngestJob.VOLUMETRIC_INGEST)
        assert (job.tile_size_x == 1024)
        assert (job.tile_size_y == 1024)
        assert (job.tile_size_z == 64)
        assert (job.tile_size_t == 1)

    def test_generate_upload_queue_args_tile_job(self):
        """Ensure ingest_type set properly"""
        self.ingest_mgr.validate_config_file(self.example_config_data)
        self.ingest_mgr.validate_properties()
        self.ingest_mgr.owner = self.user.pk
        job = self.ingest_mgr.create_ingest_job()
        actual = self.ingest_mgr._generate_upload_queue_args(job)
        assert actual['ingest_type'] == IngestJob.TILE_INGEST
        assert actual['z_chunk_size'] == 16

    def test_generate_upload_queue_args_volumetric_job(self):
        """Ensure ingest_type set properly"""
        self.ingest_mgr.validate_config_file(self.volumetric_config_data)
        self.ingest_mgr.validate_properties()
        self.ingest_mgr.owner = self.user.pk
        job = self.ingest_mgr.create_ingest_job()
        actual = self.ingest_mgr._generate_upload_queue_args(job)
        assert actual['ingest_type'] == IngestJob.VOLUMETRIC_INGEST
        assert actual['z_chunk_size'] == 64
        assert actual['ingest_queue'] is None

    def test_tile_bucket_name(self):
        """ Test get tile bucket name"""
        tile_bucket_name = self.ingest_mgr.get_tile_bucket()
        assert(tile_bucket_name is not None)
