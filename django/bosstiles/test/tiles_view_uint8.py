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
import blosc

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

from bosstiles.views import Tile, CutoutTile
from bossspatialdb.views import Cutout

from bosscore.test.setup_db import SetupTestDB
from bosscore.error import BossError

import numpy as np

from unittest.mock import patch
from mockredis import mock_strict_redis_client

import spdb
import bossutils

version = settings.BOSS_VERSION

_test_globals = {'kvio_engine': None}


class MockBossConfig(bossutils.configuration.BossConfig):
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


class MockSpatialDB(spdb.spatialdb.SpatialDB):
    """mock for redis kvio so the actual server isn't used during unit testing, but a static mockredis-py instead"""

    @patch('bossutils.configuration.BossConfig', MockBossConfig)
    @patch('redis.StrictRedis', mock_strict_redis_client)
    def __init__(self):
        super().__init__()

        if not _test_globals['kvio_engine']:
            _test_globals['kvio_engine'] = spdb.spatialdb.KVIO.get_kv_engine('redis')

        self.kvio = _test_globals['kvio_engine']


class ImageInterfaceViewTestMixin(object):

    def test_png_uint8_xy(self):
        """ Test a png xy slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/image/col1/exp1/channel1/xy/0/0:128/0:128/1/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = CutoutTile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                        orientation='xy', resolution='0', x_args='0:128', y_args='0:128', z_args='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, self.test_data_8[1, 0:128, 0:128])

    def test_png_uint8_xz(self):
        """ Test a png xz slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/image/col1/exp1/channel1/xz/0/0:128/2/0:16/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = CutoutTile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                        orientation='xz', resolution='0', x_args='0:128', y_args='2', z_args='0:16')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, np.squeeze(self.test_data_8[0:16, 2, 0:128]))

    def test_png_uint8_yz(self):
        """ Test a png yz slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/image/col1/exp1/channel1/yz/0/5/20:400/0:16/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = CutoutTile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                        orientation='yz', resolution='0', x_args='5', y_args='20:400', z_args='0:16')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, np.squeeze(self.test_data_8[0:16, 20:400, 5]))


class TestImageInterfaceView(ImageInterfaceViewTestMixin, APITestCase):

    @patch('bossutils.configuration.BossConfig', MockBossConfig)
    @patch('spdb.spatialdb.kvio.KVIO', MockSpatialDB)
    @patch('redis.StrictRedis', mock_strict_redis_client)
    def setUp(self):
        """
        Initialize the database
        :return:
        """
        # Create a user
        dbsetup = SetupTestDB()
        self.user = dbsetup.create_user('testuser')

        # Populate DB
        dbsetup.insert_spatialdb_test_data()

        # Mock config parser so dummy params get loaded (redis is also mocked)
        self.patcher = patch('bossutils.configuration.BossConfig', MockBossConfig)
        self.mock_tests = self.patcher.start()

        self.spdb_patcher = patch('spdb.spatialdb.SpatialDB', MockSpatialDB)
        self.mock_spdb = self.spdb_patcher.start()

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()
        self.mock_spdb = self.spdb_patcher.stop()

    @classmethod
    def setUpClass(cls):
        """ Setup data to read
        """
        # TODO: once cache arch allows for easily loading data in unit tests. for now just running as int test
        cls.test_data_8 = None
        pass


class TileInterfaceViewTestMixin(object):

    def test_png_uint8_xy(self):
        """ Test a png xy slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/tile/col1/exp1/channel1/xy/512/0/0/0/5/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = Tile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                  orientation='xy', tile_size='512', resolution='0',
                                  x_idx='0', y_idx='0', z_idx='5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, self.test_data_8[5, 0:512, 0:512])

    def test_png_uint8_xy_y_offset(self):
        """ Test a png xy slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/tile/col1/exp1/channel1/xy/512/0/0/1/7/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = Tile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                  orientation='xy', tile_size='512', resolution='0',
                                  x_idx='0', y_idx='1', z_idx='7')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, self.test_data_8[7, 512:1024, 0:512])

    def test_png_uint8_xy_x_offset(self):
        """ Test a png xy slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/tile/col1/exp1/channel1/xy/512/0/1/1/3/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = Tile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                  orientation='xy', tile_size='512', resolution='0',
                                  x_idx='1', y_idx='1', z_idx='3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, self.test_data_8[3, 512:1024, 512:1024])

    def test_png_uint8_xz(self):
        """ Test a png xz slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/tile/col1/exp1/channel1/xz/4/0/0/5/0/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = Tile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                  orientation='xz', tile_size='4', resolution='0',
                                  x_idx='0', y_idx='0', z_idx='5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, np.squeeze(self.test_data_8[0:4, 5, 0:4]))

    def test_png_uint8_yz(self):
        """ Test a png yz slice"""
        # Post data to the database
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/tile/col1/exp1/channel1/yz/4/0/0/7/2/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = Tile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                  orientation='yz', tile_size='4', resolution='0',
                                  x_idx='0', y_idx='7', z_idx='2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, np.squeeze(self.test_data_8[8:12, 28:32, 0]))


class TestTileInterfaceView(TileInterfaceViewTestMixin, APITestCase):

    @patch('bossutils.configuration.BossConfig', MockBossConfig)
    @patch('spdb.spatialdb.kvio.KVIO', MockSpatialDB)
    @patch('redis.StrictRedis', mock_strict_redis_client)
    def setUp(self):
        """
        Initialize the database
        :return:
        """
        # Create a user
        dbsetup = SetupTestDB()
        self.user = dbsetup.create_user('testuser')

        # Populate DB
        dbsetup.insert_spatialdb_test_data()

        # Mock config parser so dummy params get loaded (redis is also mocked)
        self.patcher = patch('bossutils.configuration.BossConfig', MockBossConfig)
        self.mock_tests = self.patcher.start()

        self.spdb_patcher = patch('spdb.spatialdb.SpatialDB', MockSpatialDB)
        self.mock_spdb = self.spdb_patcher.start()

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()
        self.mock_spdb = self.spdb_patcher.stop()

    @classmethod
    def setUpClass(cls):
        """ Setup data to read
        """
        # TODO: once cache arch allows for easily loading data in unit tests. for now just running as int test
        cls.test_data_8 = None
        pass
