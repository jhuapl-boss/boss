# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bossutils

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status
from unittest.mock import patch

from django.test.utils import override_settings
from django.conf import settings
from botocore.exceptions import ClientError

from spdb.spatialdb.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from bossobject.views import Reserve

version = settings.BOSS_VERSION

config = bossutils.configuration.BossConfig()
KVIO_SETTINGS = {"cache_host": config['aws']['cache'],
                 "cache_db": 1,
                 "read_timeout": 86400}

# state settings
STATEIO_CONFIG = {"cache_state_host": config['aws']['cache-state'],
                  "cache_state_db": 1}

# object store settings
OBJECTIO_CONFIG = {"s3_flush_queue": None,
                   "cuboid_bucket": None,
                   "page_in_lambda_function": None,
                   "page_out_lambda_function": None,
                   "s3_index_table": "intTest.{}".format(config['aws']['s3-index-table']),
                   "id_index_table": "intTest.{}".format(config['aws']['id-index-table']),
                   "id_count_table": "intTest.{}".format(config['aws']['id-count-table'])
                   }


class TestReserveIDView(APITestCase):

    @classmethod
    def setUpClass(cls):

        # Setup the helper to create temporary AWS resources
        cls.setup_helper = SetupTests()
        cls.setup_helper.mock = False

        # Create a user in django
        dbsetup = SetupTestDB()
        cls.user = dbsetup.create_user('testuser')
        dbsetup.add_role('resource-manager')
        dbsetup.set_user(cls.user)

        # Populate django models DB
        dbsetup.insert_spatialdb_test_data()

        try:
            cls.setup_helper.create_index_table(OBJECTIO_CONFIG["id_count_table"], cls.setup_helper.ID_COUNT_SCHEMA)
        except ClientError:
            cls.setup_helper.delete_index_table(OBJECTIO_CONFIG["id_count_table"])
            cls.setup_helper.create_index_table(OBJECTIO_CONFIG["id_count_table"], cls.setup_helper.ID_COUNT_SCHEMA)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.setup_helper.delete_index_table(cls.object_store_config["id_count_table"])
        except:
            pass

    @override_settings(KVIO_SETTINGS=KVIO_SETTINGS)
    @override_settings(STATEIO_CONFIG=STATEIO_CONFIG)
    @override_settings(OBJECTIO_CONFIG=OBJECTIO_CONFIG)
    def test_reserve_ids_view(self):
        """A test to reserve ids"""

        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/reserve/col1/exp1/layer1/10')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Reserve.as_view()(request, collection='col1', experiment='exp1', channel='layer1', num_ids='10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['start_id'][0], 1)
        self.assertEqual(response.data['count'], '10')