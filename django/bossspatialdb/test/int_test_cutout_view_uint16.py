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

from django.conf import settings
from unittest.mock import patch

from rest_framework.test import APITestCase

from bossspatialdb.test import CutoutInterfaceViewUint16TestMixin

from bosscore.test.setup_db import SetupTestDB
from bossutils import configuration


version = settings.BOSS_VERSION


CONFIG_UNMOCKED = configuration.BossConfig()


class MockBossIntegrationConfig:
    """A mock for BossConfig so that redis writes go to db 1 instead of the normal db 0"""
    def __init__(self):
        self.mocked_config = {}
        self.mocked_config["aws"] = {}
        self.mocked_config["aws"]["db"] = CONFIG_UNMOCKED["aws"]["cache"]
        self.mocked_config["aws"]["meta-db"] = CONFIG_UNMOCKED["aws"]["cache"]
        self.mocked_config["aws"]["cache"] = CONFIG_UNMOCKED["aws"]["cache"]
        self.mocked_config["aws"]["cache-state"] = CONFIG_UNMOCKED["aws"]["cache-state"]
        self.mocked_config["aws"]["cache-db"] = 1
        self.mocked_config["aws"]["cache-state-db"] = 1

    def read(self, filename):
        pass

    def __getitem__(self, key):
        if key == 'aws':
            return self.mocked_config[key]
        else:
            return CONFIG_UNMOCKED[key]


@patch('configparser.ConfigParser', MockBossIntegrationConfig)
class CutoutViewIntegrationTests(CutoutInterfaceViewUint16TestMixin, APITestCase):

    def setUp(self):
        """
        Initialize the database
        :return:
        """

        # Create a user
        dbsetup = SetupTestDB()
        self.user = dbsetup.create_user()

        # Populate DB
        dbsetup.insert_spatialdb_test_data()

        self.patcher = patch('configparser.ConfigParser', MockBossIntegrationConfig)
        self.mock_tests = self.patcher.start()

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()
