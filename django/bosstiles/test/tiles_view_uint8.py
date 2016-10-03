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

from bosstiles.views import Tile, Image
from bossspatialdb.views import Cutout
from spdb.project import BossResourceBasic

from bosscore.test.setup_db import SetupTestDB
from bosscore.error import BossError

import numpy as np
from PIL import Image

from unittest.mock import patch
from mockredis import mock_strict_redis_client

import spdb
import bossutils
import redis

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
        test_mat = np.random.randint(1, 254, (16, 512, 512))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Post data to the database
        factory = APIRequestFactory()

        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        force_authenticate(request, user=self.user)
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', dataset='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get an image file
        request = factory.get('/' + version + '/image/col1/exp1/channel1/xy/0/0:128/0:128/1/',
                              Accept='image/png')
        force_authenticate(request, user=self.user)
        # Make request
        response = Image.as_view()(request, collection='col1', experiment='exp1', dataset='channel1',
                                   orientation='xy', resolution='0', x_args='0:128', y_args='0:128', z_args='1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct
        test_img = Image.open(response.data)
        test_img = np.array(test_img, dtype="uint8")

        np.testing.assert_equal(test_img, test_mat[0, 0:128, 0:128])


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

        self.data = {}
        self.data['collection'] = {}
        self.data['collection']['name'] = "col1"
        self.data['collection']['description'] = "Test collection 1"

        self.data['coord_frame'] = {}
        self.data['coord_frame']['name'] = "coord_frame_1"
        self.data['coord_frame']['description'] = "Test coordinate frame"
        self.data['coord_frame']['x_start'] = 0
        self.data['coord_frame']['x_stop'] = 2000
        self.data['coord_frame']['y_start'] = 0
        self.data['coord_frame']['y_stop'] = 5000
        self.data['coord_frame']['z_start'] = 0
        self.data['coord_frame']['z_stop'] = 200
        self.data['coord_frame']['x_voxel_size'] = 4
        self.data['coord_frame']['y_voxel_size'] = 4
        self.data['coord_frame']['z_voxel_size'] = 35
        self.data['coord_frame']['voxel_unit'] = "nanometers"
        self.data['coord_frame']['time_step'] = 0
        self.data['coord_frame']['time_step_unit'] = "na"

        self.data['experiment'] = {}
        self.data['experiment']['name'] = "exp1"
        self.data['experiment']['description'] = "Test experiment 1"
        self.data['experiment']['num_hierarchy_levels'] = 7
        self.data['experiment']['hierarchy_method'] = 'slice'

        self.data['channel_layer'] = {}
        self.data['channel_layer']['name'] = "channel1"
        self.data['channel_layer']['description'] = "Test channel 1"
        self.data['channel_layer']['is_channel'] = True
        self.data['channel_layer']['datatype'] = 'uint8'
        self.data['channel_layer']['max_time_step'] = 0

        self.data['boss_key'] = 'col1&exp1&channel1'
        self.data['lookup_key'] = '4&2&1'

        self.resource = BossResourceBasic(self.data)
        self.config = bossutils.configuration.BossConfig()

        #_test_globals['kvio_engine'] = redis.StrictRedis(host=self.config["aws"]["cache"], port=6379,
         #                                                db=1,
        #                                                 decode_responses=False)

        # TODO: DMK Remove this manual loading once cache architecture is changed and supports write unit tests
        # Generate a cube
        #test_mat = np.random.randint(1, 254, (16, 512, 512))
        #test_mat = test_mat.astype(np.uint8)
        #h = test_mat.tobytes()
        #bb = blosc.compress(h, typesize=8)

        # Hand-jam it into redis
        #_test_globals['kvio_engine'].set("CACHED-CUBOID&4&2&1&0&0&0", bb)
        #_test_globals['kvio_engine'].expire("CACHED-CUBOID&4&2&1&0&0&0", 30)

    def tearDown(self):
        # Stop mocking
        self.mock_tests = self.patcher.stop()
        self.mock_spdb = self.spdb_patcher.stop()
