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
from django.test.utils import override_settings
from rest_framework.test import APITestCase

from bossspatialdb.test import CutoutInterfaceViewUint64TestMixin
from bossspatialdb.test.params import *

from bosscore.test.setup_db import SetupTestDB
import bossutils
import redis
import time
import random

from spdb.spatialdb.test.setup import SetupTests
from botocore.exceptions import ClientError


@override_settings(KVIO_SETTINGS=KVIO_SETTINGS)
@override_settings(STATEIO_CONFIG=STATEIO_CONFIG)
@override_settings(OBJECTIO_CONFIG=OBJECTIO_CONFIG)
class CutoutViewIntegration64BitTests(CutoutInterfaceViewUint64TestMixin, APITestCase):

    def setUp(self):
        """Setup to run before every test"""
        self.client.force_login(self.user)

    def tearDown(self):
        """Clean kv store in between tests"""
        client = redis.StrictRedis(host=settings.KVIO_SETTINGS["cache_host"],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=settings.STATEIO_CONFIG["cache_state_host"],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(CutoutViewIntegration64BitTests, cls).setUpClass()

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
            cls.setup_helper.create_s3_index_table(OBJECTIO_CONFIG["s3_index_table"])
        except ClientError:
            cls.setup_helper.delete_s3_index_table(OBJECTIO_CONFIG["s3_index_table"])
            cls.setup_helper.create_s3_index_table(OBJECTIO_CONFIG["s3_index_table"])

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
        super(CutoutViewIntegration64BitTests, cls).tearDownClass()
        try:
            cls.setup_helper.delete_s3_index_table(OBJECTIO_CONFIG["s3_index_table"])
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
