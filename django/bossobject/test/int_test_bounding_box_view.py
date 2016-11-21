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
import numpy as np
import blosc

from django.test.utils import override_settings
from django.conf import settings
from botocore.exceptions import ClientError

from spdb.spatialdb.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from bossobject.views import BoundingBox
from bossspatialdb.views import Cutout
import time

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
                   "cuboid_bucket": "intTest.{}".format(config['aws']['cuboid_bucket']),
                   "page_in_lambda_function": config['lambda']['page_in_function'],
                   "page_out_lambda_function": config['lambda']['flush_function'],
                   "s3_index_table": "intTest.{}".format(config['aws']['s3-index-table']),
                   "id_index_table": "intTest.{}".format(config['aws']['id-index-table']),
                   "id_count_table": "intTest.{}".format(config['aws']['id-count-table'])
                  }

_, domain = config['aws']['cuboid_bucket'].split('.', 1)
FLUSH_QUEUE_NAME = "intTest.S3FlushQueue.{}".format(domain).replace('.', '-')



class TestBoundingBoxDView(APITestCase):

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

        try:
            cls.setup_helper.create_index_table(OBJECTIO_CONFIG["s3_index_table"], cls.setup_helper.DYNAMODB_SCHEMA)
        except ClientError:
            cls.setup_helper.delete_index_table(OBJECTIO_CONFIG["s3_index_table"])
            cls.setup_helper.create_index_table(OBJECTIO_CONFIG["s3_index_table"], cls.setup_helper.DYNAMODB_SCHEMA)

        try:
            cls.setup_helper.create_index_table(OBJECTIO_CONFIG["id_index_table"], cls.setup_helper.ID_INDEX_SCHEMA)
        except ClientError:
            cls.setup_helper.delete_index_table(OBJECTIO_CONFIG["id_index_table"])
            cls.setup_helper.create_index_table(OBJECTIO_CONFIG["id_index_table"], cls.setup_helper.ID_INDEX_SCHEMA)

        try:
            cls.setup_helper.create_cuboid_bucket(OBJECTIO_CONFIG["cuboid_bucket"])
        except ClientError:
            cls.setup_helper.delete_cuboid_bucket(OBJECTIO_CONFIG["cuboid_bucket"])
            cls.setup_helper.create_cuboid_bucket(OBJECTIO_CONFIG["cuboid_bucket"])

        try:
            OBJECTIO_CONFIG["s3_flush_queue"] = cls.setup_helper.create_flush_queue(FLUSH_QUEUE_NAME)
        except ClientError:
            try:
                cls.setup_helper.delete_flush_queue(OBJECTIO_CONFIG["s3_flush_queue"])
            except:
                pass
            time.sleep(61)
            OBJECTIO_CONFIG["s3_flush_queue"] = cls.setup_helper.create_flush_queue(FLUSH_QUEUE_NAME)

    @classmethod
    def tearDownClass(cls):
        print('Deleting Temporary AWS Resources', end='', flush=True)
        try:
            cls.setup_helper.delete_index_table(cls.object_store_config["id_count_table"])
        except:
            pass
        try:
            cls.setup_helper.delete_index_table(cls.object_store_config["id_index_table"])
        except:
            pass

        try:
            cls.setup_helper.delete_index_table(OBJECTIO_CONFIG["s3_index_table"])
        except Exception as e:
            print("Failed to cleanup S3 Index Table: {}".format(e))
            pass

        try:
            cls.setup_helper.delete_cuboid_bucket(OBJECTIO_CONFIG["cuboid_bucket"])
        except Exception as e:
            print("Failed to cleanup S3 bucket: {}".format(e))
            pass

        try:
            cls.setup_helper.delete_flush_queue(OBJECTIO_CONFIG["s3_flush_queue"])
        except Exception as e:
            print("Failed to cleanup S3 flush queue: {}".format(e))
            pass

    @override_settings(KVIO_SETTINGS=KVIO_SETTINGS)
    @override_settings(STATEIO_CONFIG=STATEIO_CONFIG)
    @override_settings(OBJECTIO_CONFIG=OBJECTIO_CONFIG)
    def test_bounding_box_view(self):
        """A test to reserve ids"""

        test_mat = np.ones((128, 128, 16))
        test_mat = test_mat.astype(np.uint64)
        test_mat = test_mat.reshape((16, 128, 128))
        bb = blosc.compress(test_mat, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None)
        print (response.content)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/boundingbox/col1/exp1/layer1/0/10')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = BoundingBox.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                         resolution = '0', id='1')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
