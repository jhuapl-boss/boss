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
from pkg_resources import resource_filename

from bossingest.ingest_manager import IngestManager
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from django.contrib.auth.models import User


class BossIngestManagerTestMixin(object):

    def test_validate_ingest(self):
        """Method to test validation method"""
        # TODO: Complete after validation fully implemented
        #Validate schema and config file
        ingest_mgmr = IngestManager()
        response = ingest_mgmr.validate_config_file(self.example_config_data)
        assert (response is True)

        #Validate properties
        response = ingest_mgmr.validate_properties()
        assert (response is True)

    def test_upload_queue(self):
        """Method to test the upload_queue"""
        ingest_mgmr = IngestManager()


    def test_setup_ingest(self):
        """Method to test the setup_ingest method"""
        ingest_mgmr = IngestManager()
        ingest_job = ingest_mgmr.setup_ingest("test_user", self.example_config_data)
        assert (ingest_job is not None)

    def test_generate_upload_tasks(self):
        """"""
        print ("In the upload tasks tests:")
        ingest_mgmr = IngestManager()
        ingest_job = ingest_mgmr.setup_ingest("test_user", self.example_config_data)
        ingest_job = ingest_mgmr.generate_upload_tasks(ingest_job.id)

class TestBossIngestManager(BossIngestManagerTestMixin, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create the resources required for the ingest tests
        cls.user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(cls.user)
        dbsetup.insert_ingest_test_data()

        # Get the config_data
        config_data = SetupTests().get_ingest_config_data_dict()
        cls.example_config_data = config_data
