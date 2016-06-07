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

from bossspatialdb.test import CutoutInterfaceViewUint8TestMixin

from bosscore.test.setup_db import SetupTestDB
import bossutils

version = settings.BOSS_VERSION


class MockBossIntegrationConfig(bossutils.configuration.BossConfig):
    """Basic mock for BossConfig so 'test databases' are used for redis (1) instead of the default where real data
    can live (0)"""
    def __init__(self):
        super().__init__()
        self.config["aws"]["cache-db"] = "1"
        self.config["aws"]["cache-state-db"] = "1"

    def read(self, filename):
        pass

    def __getitem__(self, key):
        return self.config[key]


@patch('bossutils.configuration.BossConfig', MockBossIntegrationConfig)
class CutoutViewIntegrationTests(CutoutInterfaceViewUint8TestMixin, APITestCase):

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

        self.patcher = patch('bossutils.configuration.BossConfig', MockBossIntegrationConfig)
        self.mock_tests = self.patcher.start()

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()
