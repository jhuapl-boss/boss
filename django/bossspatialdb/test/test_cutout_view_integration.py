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
import os
import unittest
from unittest.mock import patch

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status

from bossspatialdb.views import Cutout

from .setup_db import SetupTestDB
from bossutils import configuration
import spdb

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


@unittest.skipIf(os.environ.get('UNIT_ONLY') is not None, "Only running unit tests")
class CutoutViewIntegrationTests(APITestCase):
    # TODO: Add proper view tests once cache is integrated, currently just making sure you get the right statuscode back

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        self.patcher = patch('configparser.ConfigParser', MockBossIntegrationConfig)
        self.mock_tests = self.patcher.start()

        # Populate db with data model stuff
        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user()
        self.client.force_login(user)
        dbsetup.insert_test_data()

        # Make sure DB is clean before testing
        cache = spdb.spatialdb.SpatialDB()
        cache.kvio.cache_client.flushdb()
        cache.kvio.status_client.flushdb()

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()

    def test_post_full_url_channel_uint8_generic(self):
        """ INTEGRATION: Test to make sure posting a block of data returns a 201
          operation - POST
          args - Full
          type - channel
          bitdepth - uin8
        :return:
            None
        """
        a = np.random.randint(0, 254, (20, 300, 500))
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

    # Commented out because mocking stomps on the logger config, so when an error occurs it can't be logged
    # TODO: Add test once logging mocking is fixed
    #def test_post_full_url_channel_uint8_generic_badurl(self):
    #    """ INTEGRATION: Test error thrown if URL params are invalid
    #      operation - POST
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
    #    request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:500/0:300/0/', bb,
    #                           content_type='application/blosc')
#
    #    response = Cutout.as_view()(request,
    #                                collection='col1',
    #                                experiment='exp1',
    #                                dataset='channel1',
    #                                resolution='0',
    #                                x_range='0:500',
    #                                y_range='0:300',
    #                                z_range='0:20')
#
    #    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Commented out because mocking stomps on the logger config, so when an error occurs it can't be logged
    # TODO: Add test once logging mocking is fixed
    #def test_post_full_url_channel_uint8_generic_missing_data(self):
    #    """ INTEGRATION: Test error thrown if data is missing
    #      operation - POST
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
    #    request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:500/0:300/0/',
    #                           content_type='application/blosc')
#
    #    response = Cutout.as_view()(request,
    #                                collection='col1',
    #                                experiment='exp1',
    #                                dataset='channel1',
    #                                resolution='0',
    #                                x_range='0:500',
    #                                y_range='0:300',
    #                                z_range='0:20')
#
    #    assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_full_url_channel_uint8_generic(self):
        """ INTEGRATION: Test to make sure getting a block of data returns a 200 and is correct
          operation - GET
          args - Full
          type - channel
          bitdepth - uin8
        :return:
            None
        """
        a = np.random.randint(0, 254, (20, 300, 500))
        a = a.astype(np.uint8)
        h = a.tobytes()
        bb = blosc.compress(h, typesize=8)

        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/1000:1500/1000:1300/0:20/', bb,
                               content_type='application/blosc')

        response = Cutout.as_view()(request,
                                    collection='col1',
                                    experiment='exp1',
                                    dataset='channel1',
                                    resolution='0',
                                    x_range='1000:1500',
                                    y_range='1000:1300',
                                    z_range='0:20')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response2 = self.client.get('/' + version + '/cutout/col1/exp1/channel1/0/1000:1500/1000:1300/0:20/',
                                    HTTP_ACCEPT='application/blosc')

        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Data should be generic blosc encoded
        response_data = blosc.decompress(response2.content)
        response_mat = np.fromstring(response_data, dtype=np.uint8)
        response_mat = np.reshape(response_mat, (20, 300, 500), order='C')

        np.testing.assert_equal(response_mat, a)

    def test_post_full_url_channel_uint8_python(self):
        """ INTEGRATION: Test POST with blosc-python interface
          operation - POST
          args - Full
          type - channel
          bitdepth - uin8
        :return:
            None
        """
        a = np.random.randint(0, 254, (20, 300, 500))
        a = a.astype(np.uint8)
        bb = blosc.pack_array(a)

        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:500/0:300/0:20/', bb,
                               content_type='application/blosc-python')

        response = Cutout.as_view()(request,
                                    collection='col1',
                                    experiment='exp1',
                                    dataset='channel1',
                                    resolution='0',
                                    x_range='0:500',
                                    y_range='0:300',
                                    z_range='0:20')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_full_url_channel_uint8_python(self):
        """ INTEGRATION: Test GET with blosc-python interface
          operation - GET
          args - Full
          type - channel
          bitdepth - uin8
        :return:
            None
        """
        a = np.random.randint(0, 254, (20, 300, 500))
        a = a.astype(np.uint8)
        bb = blosc.pack_array(a)

        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/1000:1500/1000:1300/0:20/', bb,
                               content_type='application/blosc-python')

        response = Cutout.as_view()(request,
                                    collection='col1',
                                    experiment='exp1',
                                    dataset='channel1',
                                    resolution='0',
                                    x_range='1000:1500',
                                    y_range='1000:1300',
                                    z_range='0:20')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/1000:1500/1000:1300/0:20/',
                              HTTP_ACCEPT='application/blosc-python')

        response_get = Cutout.as_view()(request,
                                        collection='col1',
                                        experiment='exp1',
                                        dataset='channel1',
                                        resolution='0',
                                        x_range='1000:1500',
                                        y_range='1000:1300',
                                        z_range='0:20')

        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        # Data should be generic blosc encoded
        response_data = blosc.unpack_array(response_get.content)

        np.testing.assert_equal(response_data, a)

