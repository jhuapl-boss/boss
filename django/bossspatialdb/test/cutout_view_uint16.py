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

from bossspatialdb.views import Cutout

from bosscore.test.setup_db import SetupTestDB
from bosscore.error import BossError

import numpy as np

from unittest.mock import patch
from mockredis import mock_strict_redis_client

import spdb
import bossutils

import os
import unittest

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


class CutoutInterfaceViewUint16TestMixin(object):
    def test_channel_uint16_wrong_data_type(self):
        """ Test posting the wrong bitdepth data """

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint16_wrong_data_type_numpy(self):
        """ Test posting the wrong bitdepth data using the blosc-numpy interface"""
        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint16_wrong_dimensions(self):
        """ Test posting with the wrong xyz dims"""

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:100/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:100', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint16_wrong_dimensions_numpy(self):
        """ Test posting with the wrong xyz dims using the numpy interface"""

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:100/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:100', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint16_get_too_big(self):
        """ Test getting a cutout that is over 1GB uncompressed"""
        # Create request
        factory = APIRequestFactory()

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/0:100000/0:100000/0:10000/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_channel_uint16_cuboid_aligned_no_offset_no_time_blosc(self):
        """ Test uint16 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 2**16-1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint16_cuboid_aligned_offset_no_time_blosc(self):
        """ Test uint16 data, cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 2**16-1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/128:256/256:384/16:32/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/128:256/256:384/16:32/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint16_cuboid_unaligned_offset_no_time_blosc(self):
        """ Test uint16 data, not cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 2**16-1, (17, 300, 500))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (17, 300, 500), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    @unittest.skipUnless(os.environ.get('RUN_HIGH_MEM_TESTS'), "Test Requires >2.5GB of Memory")
    def test_channel_uint16_cuboid_unaligned_offset_time_blosc(self):
        """ Test uint16 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2GB of memory!
        """

        test_mat = np.random.randint(1, 2**16-1, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/0:3', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/0:3',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (3, 17, 300, 500), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint16_cuboid_aligned_no_offset_no_time_blosc_numpy(self):
        """ Test uint16 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 2**16-1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint16_cuboid_aligned_offset_no_time_blosc_numpy(self):
        """ Test uint16 data, cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 2**16-1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/128:256/256:384/16:32/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/128:256/256:384/16:32/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint16_cuboid_unaligned_offset_no_time_blosc_numpy(self):
        """ Test uint16 data, not cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 2**16-1, (17, 300, 500))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    @unittest.skipUnless(os.environ.get('RUN_HIGH_MEM_TESTS'), "Test Requires >2.5GB of Memory")
    def test_channel_uint16_cuboid_unaligned_offset_time_blosc_numpy(self):
        """ Test uint16 data, not cuboid aligned, offset, time samples, blosc interface"""

        test_mat = np.random.randint(1, 2**16-1, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/0:3', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/100:600/450:750/20:37/0:3',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    @unittest.skipUnless(os.environ.get('RUN_HIGH_MEM_TESTS'), "Test Requires >2.5GB of Memory")
    def test_channel_uint16_cuboid_unaligned_offset_time_offset_blosc_numpy(self):
        """ Test uint16 data, not cuboid aligned, offset, time samples, blosc interface"""

        test_mat = np.random.randint(1, 2**16-1, (3, 17, 225, 200))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/100:300/450:675/20:37/203:206/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:300', y_range='450:675', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/100:300/450:675/20:37/203:206/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='100:300', y_range='450:675', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)


@patch('redis.StrictRedis', mock_strict_redis_client)
@patch('bossutils.configuration.BossConfig', MockBossConfig)
@patch('spdb.spatialdb.kvio.KVIO', MockSpatialDB)
class TestCutoutInterfaceView(CutoutInterfaceViewUint16TestMixin, APITestCase):

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
