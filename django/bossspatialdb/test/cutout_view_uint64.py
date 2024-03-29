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

from unittest.mock import patch
from fakeredis import FakeStrictRedis

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
    @patch('redis.StrictRedis', FakeStrictRedis)
    def __init__(self):
        super().__init__()

        if not _test_globals['kvio_engine']:
            _test_globals['kvio_engine'] = spdb.spatialdb.KVIO.get_kv_engine('redis')

        self.kvio = _test_globals['kvio_engine']


class CutoutInterfaceViewUint64TestMixin(object):

    def test_channel_uint64_wrong_data_type(self):
        """ Test posting the wrong bitdepth data """

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint64_wrong_data_type_numpy(self):
        """ Test posting the wrong bitdepth data using the blosc-numpy interface"""
        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint64_wrong_dimensions(self):
        """ Test posting with the wrong xyz dims"""

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:100/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:100', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint64_wrong_dimensions_numpy(self):
        """ Test posting with the wrong xyz dims using the numpy interface"""

        test_mat = np.random.randint(1, 2 ** 16 - 1, (16, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:100/0:128/0:16/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:100', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_channel_uint64_get_too_big(self):
        """ Test getting a cutout that is over 1GB uncompressed"""
        # Create request
        factory = APIRequestFactory()

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:2048/0:2048/0:66/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:2048', y_range='0:2048', z_range='0:66', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_channel_uint64_cuboid_aligned_no_offset_no_time_blosc(self):
        """ Test uint64 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 256, (4, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (4, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_cuboid_aligned_offset_no_time_blosc(self):
        """ Test uint64 data, cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 256, (4, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (4, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_filter_by_id(self):
        """ Test filter_cutout by ids not in the region - one id"""

        test_mat = np.ones((128, 128, 4))
        test_mat = test_mat.reshape(4, 128, 128)
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/?filter=1',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (4, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)
        np.testing.assert_array_equal(np.unique(data_mat), np.arange(1, 2, dtype=np.uint64))

    def test_channel_uint64_filter_multiple_ids(self):
        """ Test filter_cutout by ids - multiple ids in the filter list"""

        test_mat = np.ones((128, 128, 4))
        test_mat[0][0][0] = 2
        test_mat[0][0][1] = 3
        test_mat[0][0][2] = 4
        test_mat = test_mat.reshape(4, 128, 128)
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/?filter=1,2,3',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (4, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(np.unique(data_mat), np.arange(0, 4, dtype=np.uint64))

    def test_channel_uint64_filter_include_ids_not_in_region(self):
        """ Test filter_cutout by ids - only one id found in the cutout"""

        test_mat = np.ones((128, 128, 4))
        test_mat[0][0][0] = 2
        test_mat[0][0][1] = 3
        test_mat[0][0][2] = 4
        test_mat = test_mat.reshape(4, 128, 128)
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/?filter=1,6,7',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (4, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(np.unique(data_mat), np.arange(0, 2, dtype=np.uint64))

    def test_channel_uint64_filter_ids_not_found(self):
        """ Test filter_cutout by ids not in the region"""

        test_mat = np.ones((128, 128, 4))
        test_mat[0][0][0] = 2
        test_mat[0][0][1] = 3
        test_mat[0][0][2] = 4
        test_mat = test_mat.reshape(4, 128, 128)
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/?filter=5,6,7',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (4, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(np.unique(data_mat), np.arange(0, 1, dtype=np.uint64))

    @unittest.skipUnless(settings.RUN_HIGH_MEM_TESTS, "Test Requires >2.5GB of Memory")
    def test_channel_uint64_cuboid_unaligned_offset_no_time_blosc(self):
        """ Test uint64 data, not cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 256, (17, 300, 500))
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:37/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:37/',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (17, 300, 500), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    @unittest.skipUnless(settings.RUN_HIGH_MEM_TESTS, "Test Requires >2.5GB of Memory")
    def test_channel_uint64_cuboid_unaligned_offset_time_blosc(self):
        """ Test uint64 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2.5GB of memory!
        """

        test_mat = np.random.randint(1, 256, (2, 17, 300, 280))
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/100:380/450:750/20:37/0:2', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:380', y_range='450:750', z_range='20:37', t_range='0:2')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/100:380/450:750/20:37/0:2',
                              HTTP_ACCEPT='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:380', y_range='450:750', z_range='20:37', t_range='0:2').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (2, 17, 300, 280), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_cuboid_aligned_no_offset_no_time_blosc_numpy(self):
        """ Test uint64 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.random.randint(1, 256, (4, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_cuboid_aligned_offset_no_time_blosc_numpy(self):
        """ Test uint64 data, cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 256, (4, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/128:256/256:384/16:20/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:20', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_cuboid_unaligned_offset_no_time_blosc_numpy(self):
        """ Test uint64 data, not cuboid aligned, offset, no time samples, blosc interface"""

        test_mat = np.random.randint(1, 256, (4, 300, 500))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:24/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:24', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:24/',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:24', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    @unittest.skipUnless(settings.RUN_HIGH_MEM_TESTS, "Test Requires >2.5GB of Memory")
    def test_channel_uint64_cuboid_unaligned_offset_time_blosc_numpy(self):
        """ Test uint64 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2GB of memory!
        """

        test_mat = np.random.randint(1, 256, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:37/0:3', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='0:3')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:37/0:3',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='0:3').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    @unittest.skipUnless(settings.RUN_HIGH_MEM_TESTS, "Test Requires >2.5GB of Memory")
    def test_channel_uint64_cuboid_unaligned_offset_time_offset_blosc_numpy(self):
        """ Test uint64 data, not cuboid aligned, offset, time samples, blosc interface

        Test Requires >=2GB of memory!
        """

        test_mat = np.random.randint(1, 256, (3, 17, 300, 500))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:37/200:203', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='200:203')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/100:600/450:750/20:37/200:203',
                              HTTP_ACCEPT='application/blosc-python')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='100:600', y_range='450:750', z_range='20:37', t_range='200:203').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_mat = blosc.unpack_array(response.content)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_notime_npygz_download(self):
        """ Test uint8 data, using the npygz interface
        """
        test_mat = np.random.randint(1, 256, (4, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4',
                                    t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_time_npygz_download(self):
        """ Test uint8 data, using the npygz interface with time series support

        """
        test_mat = np.random.randint(1, 256, (3, 4, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        bb = blosc.pack_array(test_mat)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/10:13', bb,
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4',
                                    t_range='10:13')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/10:13',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4',
                                    t_range='10:13').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_notime_npygz_upload(self):
        """ Test uint8 data, using the npygz interface while uploading in that format as well
        """
        test_mat = np.random.randint(1, 256, (4, 128, 128))
        test_mat = test_mat.astype(np.uint64)

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
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/', npy_gz_file.read(),
                               content_type='application/npygz')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4',
                                    t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_time_npygz_upload(self):
        """ Test uint8 data, using the npygz interface with time series support while uploading in that format as well

        """
        test_mat = np.random.randint(1, 256, (3, 4, 128, 128))
        test_mat = test_mat.astype(np.uint64)

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
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/10:13', npy_gz_file.read(),
                               content_type='application/npygz')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4',
                                    t_range='10:13')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:4/10:13',
                              HTTP_ACCEPT='application/npygz')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:4',
                                    t_range='10:13').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        data_bytes = zlib.decompress(response.content)

        # Open
        data_obj = io.BytesIO(data_bytes)
        data_mat = np.load(data_obj)

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)


@patch('redis.StrictRedis', FakeStrictRedis)
@patch('bossutils.configuration.BossConfig', MockBossConfig)
@patch('spdb.spatialdb.kvio.KVIO', MockSpatialDB)
class TestCutoutInterfaceView(CutoutInterfaceViewUint64TestMixin, APITestCase):

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
