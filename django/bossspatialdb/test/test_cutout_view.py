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
import numpy as np
import blosc

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status

from bossspatialdb.views import Cutout

from .setup_db import SetupTestDB

import unittest
from unittest.mock import patch
from mockredis import mock_strict_redis_client

import spdb

version = settings.BOSS_VERSION


class MockBossConfig:
    """Basic mock for BossConfig to contain the properties needed for this test"""
    def __init__(self):
        self.config = {}
        self.config["aws"] = {}
        self.config["aws"]["meta-db"] = {"https://meta.url.com"}
        self.config["aws"]["cache"] = {"https://some.url.com"}
        self.config["aws"]["cache-state"] = {"https://some.url2.com"}
        self.config["aws"]["cache-db"] = 1
        self.config["aws"]["cache-state-db"] = 1

    def read(self, filename):
        pass

    def __getitem__(self, key):
        return self.config[key]


class MockKVIO:
    """Basic mock for BossConfig to contain the properties needed for this test"""

    @patch('configparser.ConfigParser', MockBossConfig)
    @patch('redis.StrictRedis', mock_strict_redis_client)
    def __init__(self):
        self.static_kvio = spdb.spatialdb.KVIO.get_kv_engine('redis')

    @patch('configparser.ConfigParser', MockBossConfig)
    @patch('redis.StrictRedis', mock_strict_redis_client)
    def get_kv_engine(self, param):
        return self.static_kvio


@patch('redis.StrictRedis', mock_strict_redis_client)
@patch('configparser.ConfigParser', MockBossConfig)
@patch('spdb.spatialdb.kvio.KVIO', MockKVIO)
class CutoutInterfaceViewTests(APITestCase):
    # TODO: Add proper view tests once cache is integrated, currently just making sure you get the right statuscode back

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        # Populate db with data model stuff
        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        self.client.force_login(user)
        dbsetup.insert_test_data()

        # Mock config parser so dummy params get loaded (redis is also mocked)
        self.patcher = patch('configparser.ConfigParser', MockBossConfig)
        self.mock_tests = self.patcher.start()

        self.kvio_patcher = patch('spdb.spatialdb.kvio.KVIO', MockKVIO)
        self.mock_KVIO = self.kvio_patcher.start()

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()
        self.mock_KVIO = self.kvio_patcher.stop()

    def test_post_full_url_channel_uint8_generic(self):
        """ Test to make sure posting a block of data returns a 201
          operation - POST
          args - Full
          type - channel
          bitdepth - uin8
        :return:
            None
        """
        a = np.random.randint(0, 254, (500, 300, 20))
        a = a.astype(np.uint8)
        h = a.tobytes()
        bb = blosc.compress(h, typesize=8)

        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:500/0:300/0:20/', bb,
                               content_type='application/blosc')

        response = Cutout.as_view()(request,
                                    collection='col1',
                                    experiment='exp1',
                                    dataset='channel1',
                                    resolution='0',
                                    x_range='0:500',
                                    y_range='0:300',
                                    z_range='0:20')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # TODO: Finish unit tests once mocking is properly configured so mockredis instance is persistent
    #def test_get_full_url_channel_uint8_generic(self):
    #    """ Test to make sure getting a block of data returns a 200 and is correct
    #      operation - GET
    #      args - Full
    #      type - channel
    #      bitdepth - uin8
    #    :return:
    #        None
    #    """
    #    a = np.random.randint(0, 254, (500, 300, 20))
    #    a = a.astype(np.uint8)
    #    h = a.tobytes()
    #    bb = blosc.compress(h, typesize=8)
#
    #    factory = APIRequestFactory()
    #    request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/1000:1500/1000:1300/0:20/', bb,
    #                           content_type='application/blosc')
#
    #    response = Cutout.as_view()(request,
    #                                collection='col1',
    #                                experiment='exp1',
    #                                dataset='channel1',
    #                                resolution='0',
    #                                x_range='1000:1500',
    #                                y_range='1000:1300',
    #                                z_range='0:20')
#
    #    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#
    #    factory = APIRequestFactory()
    #    request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/1000:1500/1000:1300/0:20/',
    #                          content_type='application/blosc')
#
    #    response = Cutout.as_view()(request,
    #                                collection='col1',
    #                                experiment='exp1',
    #                                dataset='channel1',
    #                                resolution='0',
    #                                x_range='1000:1500',
    #                                y_range='1000:1300',
    #                                z_range='0:20')
#
    #    self.assertEqual(response.status_code, status.HTTP_200_OK)
#
    #    # Assuming came back generic blosc since we didn't specify
    #    response_data = blosc.decompress(response.data)
    #    response_mat = np.fromstring(response_data, dtype=np.uint8)
    #    response_mat = np.reshape(response_mat, (500, 300, 20), order='C')



    #def test_view_token_cutout_post(self):
    #    """
    #    Test to make sure posting a block of data returns a 201
    #    :return:
    #    """
    #    a = np.random.randint(0, 100, (5, 6, 2))
    #    h = a.tobytes()
    #    bb = blosc.compress(h, typesize=8)
#
    #    response = self.client.post('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1', bb,
    #                                content_type='application/octet-stream')
#
    #    # TODO: Once views are implemented need to finish test and switch to 200
    #    #self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#
    #def test_full_token_cutout_get(self):
    #    """
    #    Test to make sure getting a block of data returns a 200
    #    :return:
    #    """
    #    response = self.client.get('/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2',
    #                               content_type='application/octet-stream')
#
    #    self.assertEqual(response.status_code, status.HTTP_200_OK)
#
    #def test_view_token_cutout_get(self):
    #    """
    #    Test to make sure getting a block of data returns a 200
    #    :return:
    #    """
    #    response = self.client.get('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1',
    #                               content_type='application/octet-stream')
#
    #    # TODO: Once views are implemented need to finish test and switch to 200
    #    #self.assertEqual(response.status_code, status.HTTP_200_OK)
    #    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#
    #def test_view_token_cutout_get_missing_token_error(self):
    #    """
    #    Test to make sure you get an error
    #    :return:
    #    """
    #    response = self.client.get('/' + version + '/cutout/2/0:5/0:6/0:2',
    #                               content_type='application/octet-stream')
#
    #    self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
#