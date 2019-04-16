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
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

from bosstiles.test.tiles_view_uint8 import ImageInterfaceViewTestMixin, TileInterfaceViewTestMixin

from bosscore.test.setup_db import DjangoSetupLayer
from bossspatialdb.views import Cutout
from bosstiles.views import Tile, CutoutTile

import numpy as np
import blosc
import redis
import time

version = settings.BOSS_VERSION


class ImageViewIntegrationTests(ImageInterfaceViewTestMixin, APITestCase):
    layer = DjangoSetupLayer
    test_data_loaded = False

    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        # Log Django User in
        self.client.force_login(self.user)

        if not self.test_data_loaded:
            # Flush cache between tests
            client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                       port=6379, db=1, decode_responses=False)
            client.flushdb()
            client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                       port=6379, db=1, decode_responses=False)
            client.flushdb()

            # load some data for reading
            self.test_data_8 = np.random.randint(1, 254, (16, 1024, 1024), dtype=np.uint8)
            bb = blosc.compress(self.test_data_8, typesize=8)

            # Post data to the database
            factory = APIRequestFactory()
            request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:1024/0:1024/0:16/', bb,
                                   content_type='application/blosc')
            force_authenticate(request, user=self.user)
            _ = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                 resolution='0', x_range='0:1024', y_range='0:1024', z_range='0:16', t_range=None)
            self.test_data_loaded = True

    def test_no_cache_read(self):
        """Test no-cache option when reading an image"""
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/image/col1/exp1/channel1/xy/0/400:700/300:800/3/?no-cache=true',
                              Accept='image/png')
        force_authenticate(request, user=self.user)

        time.sleep(10)

        # Make request
        response = CutoutTile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                        orientation='xy', resolution='0', x_args='400:700', y_args='300:800',
                                        z_args='3')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, self.test_data_8[3, 300:800, 400:700])


class TileViewIntegrationTests(TileInterfaceViewTestMixin, APITestCase):
    layer = DjangoSetupLayer
    test_data_loaded = False

    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        # Log Django User in
        self.client.force_login(self.user)

        if not self.test_data_loaded:
            # Flush cache between tests
            client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                       port=6379, db=1, decode_responses=False)
            client.flushdb()
            client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                       port=6379, db=1, decode_responses=False)
            client.flushdb()

            # load some data for reading
            self.test_data_8 = np.random.randint(1, 254, (16, 1024, 1024), dtype=np.uint8)
            bb = blosc.compress(self.test_data_8, typesize=8)

            # Post data to the database
            factory = APIRequestFactory()
            request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:1024/0:1024/0:16/', bb,
                                   content_type='application/blosc')
            force_authenticate(request, user=self.user)
            _ = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                 resolution='0', x_range='0:1024', y_range='0:1024', z_range='0:16', t_range=None)
            self.test_data_loaded = True

    def test_no_cache_read(self):
        """Test no-cache option when reading an image"""
        factory = APIRequestFactory()

        # Get an image file
        request = factory.get('/' + version + '/tile/col1/exp1/channel1/xy/512/0/0/0/5/?no-cache=true',
                              Accept='image/png')
        force_authenticate(request, user=self.user)

        time.sleep(10)

        # Make request
        response = Tile.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                  orientation='xy', tile_size='512', resolution='0',
                                  x_idx='0', y_idx='0', z_idx='5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check data is correct (this is pre-renderer)
        test_img = np.array(response.data, dtype="uint8")

        np.testing.assert_equal(test_img, self.test_data_8[5, 0:512, 0:512])

    def tearDown(self):
        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()


