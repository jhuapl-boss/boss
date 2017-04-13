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
import zlib
import io
from PIL import Image

from unittest.mock import patch
from mockredis import mock_strict_redis_client

import spdb
import bossutils
from spdb.spatialdb.rediskvio import RedisKVIO
from spdb.spatialdb.state import CacheStateDB
from spdb.spatialdb.spatialdb import SpatialDB
from spdb.spatialdb.object import AWSObjectStore


version = settings.BOSS_VERSION

_test_globals = {'cache': None,
                 'state': None}

# DMK - can be removed once proper mocking is completed
#class MockBossConfig(bossutils.configuration.BossConfig):
#    """Basic mock for BossConfig so 'test databases' are used for redis (1) instead of the default where real data
#    can live (0)"""
#    def __init__(self):
#        super().__init__()
#        self.config["aws"]["cache-db"] = "1"
#        self.config["aws"]["cache-state-db"] = "1"
#
#    def read(self, filename):
#        pass
#
#    def __getitem__(self, key):
#        return self.config[key]
#
#
#class MockSpatialDB(spdb.spatialdb.spatialdb.SpatialDB):
#    """mock for redis kvio so the actual server isn't used during unit testing, but a static mockredis-py instead"""
#
#    def __init__(self, kv_conf, state_conf, object_store_conf):
#        SpatialDB.__init__(kv_conf, state_conf, object_store_conf)
#        if not _test_globals['cache']:
#            _test_globals['cache'] = RedisKVIO(kv_conf)
#            _test_globals['state'] = CacheStateDB(state_conf)
#
#        self.kvio = _test_globals['cache']
#        self.cache_state = _test_globals['state']


@patch('redis.StrictRedis', mock_strict_redis_client)
def mock_init_(self, kv_conf, state_conf, object_store_conf):
    print("init mocker")
    self.kv_config = kv_conf
    self.state_conf = state_conf
    self.object_store_config = object_store_conf

    # Threshold number of cuboids for using lambda on reads
    self.read_lambda_threshold = 600  # Currently high since read lambda not implemented
    # Number of seconds to wait for dirty cubes to get clean
    self.dirty_read_timeout = 60

    if not _test_globals['cache']:
        kv_conf["cache_db"] = 1
        state_conf["cache_state_db"] = 1
        print(kv_conf)
        print(state_conf)
        _test_globals['cache'] = RedisKVIO(kv_conf)
        _test_globals['state'] = CacheStateDB(state_conf)

    self.kvio = _test_globals['cache']
    self.cache_state = _test_globals['state']
    self.objectio = AWSObjectStore(object_store_conf)


class CutoutInterfaceViewUint8TestMixin(object):

    def test_channel_uint8_wrong_data_type(self):
        """ Test posting the wrong bitdepth data """

        config = bossutils.configuration.BossConfig()

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint8_wrong_data_type_numpy(self):
        """ Test posting the wrong bitdepth data using the blosc-numpy interface"""
        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint8_wrong_dimensions(self):
        """ Test posting with the wrong xyz dims"""

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:100/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:100', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint8_wrong_dimensions_numpy(self):
        """ Test posting with the wrong xyz dims using the numpy interface"""

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:100/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:100', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint8_get_too_big(self):
        """ Test getting a cutout that is over 1GB uncompressed"""
        # Create request
        factory = APIRequestFactory()

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/0:2048/0:2048/0:131/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:2048', y_range='0:2048', z_range='0:131', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_channel_uint8_cuboid_aligned_no_offset_no_time_blosc(self):
        """ Test uint8 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_aligned_no_offset_no_time_blosc_4d(self):
        """ Test uint8 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 254, (1, 16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/3:4/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range="3:4")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/3:4/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range="3:4").render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (1, 16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_aligned_offset_no_time_blosc(self):
        """ Test uint8 data, cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/128:256/256:384/16:32/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/128:256/256:384/16:32/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_unaligned_offset_no_time_blosc(self):
        """ Test uint8 data, not cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 254, (17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (17, 300, 500), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_unaligned_offset_time_blosc(self):
        """ Test uint8 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2GB of memory!
        """

        test_mat = np.random.randint(1, 254, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/0:3', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='0:3')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/0:3',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='0:3').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (3, 17, 300, 500), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_aligned_no_offset_no_time_blosc_numpy(self):
        """ Test uint8 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_aligned_offset_no_time_blosc_numpy(self):
        """ Test uint8 data, cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/128:256/256:384/16:32/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/128:256/256:384/16:32/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_unaligned_offset_no_time_blosc_numpy(self):
        """ Test uint8 data, not cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 254, (17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_unaligned_offset_time_blosc_numpy(self):
        """ Test uint8 data, not cuboid aligned, offset, time samples, blosc interface
        """

        test_mat = np.random.randint(1, 254, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/0:3', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='0:3')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/0:3',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='0:3').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_unaligned_offset_time_offset_blosc_numpy(self):
        """ Test uint8 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2GB of memory!
        """

        test_mat = np.random.randint(1, 254, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/200:203', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='200:203')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/200:203',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range='200:203').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_unaligned_offset_time_offset_overwrite_blosc__numpy(self):
        """ Test uint8 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2GB of memory!
        """
        # Do this a couple times to the same region....should succeed every time
        for _ in range(0, 2):
            test_mat = np.random.randint(1, 254, (3, 17, 300, 500))
            test_mat = test_mat.astype(np.uint8)
            bb = blosc.pack_array(test_mat)

            # Create request
            factory = APIRequestFactory()
            request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/40:57/200:203', bb,
                                   content_type='application/blosc-python')
            # log in user
            force_authenticate(request, user=self.user)

            # Make request
            response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                        resolution='0', x_range='100:600', y_range='450:750', z_range='40:57',
                                        t_range='200:203')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            # Create Request to get data you posted
            request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/40:57/200:203',
                                  HTTP_ACCEPT='application/blosc-python')

            # log in user
            force_authenticate(request, user=self.user)

            # Make request
            response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                        resolution='0', x_range='100:600', y_range='450:750', z_range='40:57',
                                        t_range='200:203').render()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Decompress
            data_mat = blosc.unpack_array(response.content)

            # Test for data equality (what you put in is what you got back!)
            np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_notime_npygz_download(self):
        """ Test uint8 data, using the npygz interface
        """
        test_mat = np.random.randint(1, 254, (17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make POST data
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request to GET data
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_time_npygz_download(self):
        """ Test uint8 data, using the npygz interface with time series support

        """

        test_mat = np.random.randint(1, 254, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/100:103', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range='100:103')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/100:103',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range='100:103').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_notime_npygz_upload(self):
        """ Test uint8 data, using the npygz interface while uploading in that format as well
        """
        test_mat = np.random.randint(1, 254, (17, 300, 500))
        test_mat = test_mat.astype(np.uint8)

        # Save Data to npy
        npy_file = io.BytesIO()
        np.save(npy_file, test_mat, allow_pickle=False)

        # Compress npy
        npy_gz = zlib.compress(npy_file.getvalue())

        # Send file
        npy_gz_file = io.BytesIO(npy_gz)
        npy_gz_file.seek(0)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/',
                               npy_gz_file.read(),
                               content_type='application/npygz')
        # log in user
        force_authenticate(request, user=self.user)

        # Make POST data
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request to GET data
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_time_npygz_upload(self):
        """ Test uint8 data, using the npygz interface with time series support while uploading in that format as well

        """
        test_mat = np.random.randint(1, 254, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint8)

        # Save Data to npy
        npy_file = io.BytesIO()
        np.save(npy_file, test_mat, allow_pickle=False)

        # Compress npy
        npy_gz = zlib.compress(npy_file.getvalue())

        # Send file
        npy_gz_file = io.BytesIO(npy_gz)
        npy_gz_file.seek(0)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/150:153',
                               npy_gz_file.read(),
                               content_type='application/npygz')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range='150:153')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/100:600/450:750/20:37/150:153',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37',
                                    t_range='150:153').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_aligned_offset_no_time_jpeg(self):
        """ Test uint8 data, cuboid aligned, offset, no time samples, jpeg interface"""

        test_mat = np.random.randint(1, 254, (16, 1024, 512))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/2560:3072/2560:3584/32:48/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='2560:3072', y_range='2560:3584', z_range='32:48',
                                    t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request2 = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/2560:3072/2560:3584/32:48/',
                               HTTP_ACCEPT='image/jpeg')
        # log in user
        force_authenticate(request2, user=self.user)

        # Make request
        response = Cutout.as_view()(request2, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='2560:3072', y_range='2560:3584', z_range='32:48',
                                    t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Load image
        jpeg_img = Image.open(io.BytesIO(response.content))
        img_array = np.array(jpeg_img)

        # Make sure the correct dimensions
        self.assertEqual((1024 * 16, 512), img_array.shape)

        # Reshape input
        input_shape = test_mat.shape
        check_mat = np.reshape(test_mat, (input_shape[0] * input_shape[1], input_shape[2]), order="C")

        # Save to Image
        check_image = Image.fromarray(check_mat)
        img_file = io.BytesIO()
        check_image.save(img_file, "JPEG", quality=85)

        # Decode to matrix
        img_file.seek(0)
        check_image_mat = Image.open(img_file)

        # Make sure data is the same
        np.testing.assert_equal(np.array(check_image_mat), img_array)

    def test_channel_uint8_jpeg_invalid_4d(self):
        """ Test jpeg interface does not support 4D cutouts"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/2560:3072/2560:3584/32:48/3:5/',
                              HTTP_ACCEPT='image/jpeg')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='2560:3072', y_range='2560:3584', z_range='32:48',
                                    t_range='3:5').render()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint8_jpeg_invalid_datatype(self):
        """ Test jpeg interface does not support 4D cutouts"""
        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/2560:3072/2560:3584/32:48/',
                              HTTP_ACCEPT='image/jpeg')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='2560:3072', y_range='2560:3584', z_range='32:48',
                                    t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint8_downsample_below_iso_fork(self):
        """ Test writing/reading data to non-base resolution below the iso fork"""

        self.dbsetup.insert_downsample_data()

        test_mat = np.random.randint(1, 254, (17, 300, 500))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp_ds_aniso/channel1/1/100:600/450:750/20:37/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso/channel1/0/100:600/450:750/20:37/',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='0', x_range='100:600', y_range='450:750',
                                    z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (17, 300, 500), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_downsample_above_iso_fork(self):
        """ Test writing/reading data to non-base resolution above the iso fork"""
        self.dbsetup.insert_downsample_data()
        self.dbsetup.insert_downsample_write_data()

        test_mat = np.random.randint(1, 254, (2, 256, 256))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp_ds_aniso_4/channel1/4/0:256/0:256/2:4/?iso=true', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso_4', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256', z_range='2:4', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted, but ask for aniso data
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso_4/channel1/4/0:256/0:256/2:4/?iso=false',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso_4', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256',
                                    z_range='2:4', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (2, 256, 256), order='C')

        # Should be 0 at non-iso, since you wrote directly to iso level
        self.assertEqual(data_mat.sum(), 0)

        # Create Request to get data you posted, but ask for iso data
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso_4/channel1/4/0:256/0:256/2:4/?iso=true',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso_4', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256',
                                    z_range='2:4', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (2, 256, 256), order='C')

        # Should be 0 at non-iso, since you wrote directly to iso level
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_downsample_above_iso_fork_isotropic(self):
        """ Test writing/reading data to non-base resolution above the iso fork with an isotropic channel"""
        self.dbsetup.insert_downsample_data()
        self.dbsetup.insert_downsample_write_data()

        test_mat = np.random.randint(1, 254, (2, 256, 256))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp_ds_iso_4/channel1/4/0:256/0:256/2:4/?iso=true', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_iso_4', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256', z_range='2:4', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted, but ask for aniso data
        request = factory.get('/' + version + '/cutout/col1/exp_ds_iso_4/channel1/4/0:256/0:256/2:4/?iso=false',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_iso_4', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256',
                                    z_range='2:4', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (2, 256, 256), order='C')

        # Should be equal to what you wrote (data is only isotropic)
        np.testing.assert_array_equal(data_mat, test_mat)

        # Create Request to get data you posted, but ask for iso data
        request = factory.get('/' + version + '/cutout/col1/exp_ds_iso_4/channel1/4/0:256/0:256/2:4/?iso=true',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_iso_4', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256',
                                    z_range='2:4', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (2, 256, 256), order='C')

        # Should be equal to what you wrote (data is only isotropic)
        np.testing.assert_array_equal(data_mat, test_mat)

# @patch('bossutils.configuration.BossConfig', new=MockBossConfig)
# @patch('redis.StrictRedis', new=mock_strict_redis_client)
# @patch('spdb.spatialdb.spatialdb.SpatialDB', MockSpatialDB)
@patch('spdb.spatialdb.SpatialDB.__init__', mock_init_)
class TestCutoutInterfaceView(CutoutInterfaceViewUint8TestMixin, APITestCase):

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        # Create a user
        self.dbsetup = SetupTestDB()
        self.user = self.dbsetup.create_user('testuser')

        # Populate DB
        self.dbsetup.insert_spatialdb_test_data()

        # Mock config parser so dummy params get loaded (redis is also mocked)
        #self.patcher = patch('bossutils.configuration.BossConfig', MockBossConfig)
        #self.mock_tests = self.patcher.start()

        ##self.mock_redis = self.redis_patcher.start()

        #self.spdb_patcher = patch('spdb.spatialdb.spatialdb.SpatialDB', mock_init_)
        #self.mock_spdb = self.spdb_patcher.start()

    def tearDown(self):
        # Stop mocking
        #self.patcher.stop()
        #self.spdb_patcher.stop()
        #self.redis_patcher.stop()
        pass
