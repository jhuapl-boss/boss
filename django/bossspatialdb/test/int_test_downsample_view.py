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

from bossspatialdb.views import Downsample
from bossspatialdb.test import DownsampleInterfaceViewMixin
from bossspatialdb.views import Cutout

from bosscore.test.setup_db import DjangoSetupLayer


from bosscore.test.setup_db import SetupTestDB
from bosscore.error import BossError
import json
from unittest.mock import patch
import time
import redis
import bossutils
import blosc
import numpy as np

version = settings.BOSS_VERSION

_global_mocked_config_data = bossutils.configuration.BossConfig()


def mock_boss_cfg():
    return _global_mocked_config_data


@patch('bossutils.configuration.BossConfig', mock_boss_cfg)
class TestIntegrationDownsampleInterfaceView(DownsampleInterfaceViewMixin, APITestCase):
    layer = DjangoSetupLayer

    def test_start_downsample_get_status_and_check_data(self):
        """A large complex test that verifies all the pluming for downsample.
         Does not validate data integrity, but does make sure data exists at different levels and iso vs. aniso."""

        self.dbsetup.insert_downsample_data()

        # Post some data to the channel
        test_mat = np.random.randint(1, 254, (16, 1024, 1024))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp_ds_aniso/channel1/0/0:1024/0:1024/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='0', x_range='0:1024', y_range='0:1024', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Wait for data to be written
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso/channel1/0/0:1024/0:1024/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='0', x_range='0:1024', y_range='0:1024',
                                    z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Trigger downsample
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                               content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make Sure status has changed
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 5)
        self.assertEqual(response.data["status"], "IN_PROGRESS")

        for _ in range(0, 30):
            # Make request
            response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                            channel='channel1').render()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            if response.data["status"] != "IN_PROGRESS":
                break

            time.sleep(2)

        # Verify now downsampled
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 5)
        self.assertEqual(response.data["status"], "DOWNSAMPLED")

        # Get data at res 1 and verify it's non-zero
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso/channel1/1/0:512/0:512/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='1', x_range='0:512', y_range='0:512',
                                    z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        raw_data = blosc.decompress(response.content)
        data_mat_res1_aniso = np.fromstring(raw_data, dtype=np.uint8)
        data_mat_res1_aniso = np.reshape(data_mat_res1_aniso, (16, 512, 512), order='C')

        # Make sure not blank
        self.assertGreater(data_mat_res1_aniso.sum(), 100)

        # Get data at res 1 with iso flag and verify it's non-zero and the same as without flag
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso/channel1/1/0:512/0:512/0:16/?iso=true',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='1', x_range='0:512', y_range='0:512',
                                    z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        raw_data = blosc.decompress(response.content)
        data_mat_res1_iso = np.fromstring(raw_data, dtype=np.uint8)
        data_mat_res1_iso = np.reshape(data_mat_res1_iso, (16, 512, 512), order='C')

        # Make sure not blank
        self.assertGreater(data_mat_res1_iso.sum(), 100)
        np.testing.assert_array_equal(data_mat_res1_iso, data_mat_res1_aniso)

        # Get data at res 4 with iso flag and verify it's non-zero and DIFFERENT than without flag
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso/channel1/4/0:256/0:256/0:8/?iso=false',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256',
                                    z_range='0:8', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        raw_data = blosc.decompress(response.content)
        data_mat_res4_aniso = np.fromstring(raw_data, dtype=np.uint8)
        data_mat_res4_aniso = np.reshape(data_mat_res4_aniso, (8, 256, 256), order='C')

        # Make sure not blank
        self.assertGreater(data_mat_res4_aniso.sum(), 1)

        # Get data at res 4 with iso flag and verify it's non-zero and DIFFERENT than without flag
        request = factory.get('/' + version + '/cutout/col1/exp_ds_aniso/channel1/4/0:256/0:256/0:8/?iso=true',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='4', x_range='0:256', y_range='0:256',
                                    z_range='0:8', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        raw_data = blosc.decompress(response.content)
        data_mat_res4_iso = np.fromstring(raw_data, dtype=np.uint8)
        data_mat_res4_iso = np.reshape(data_mat_res4_iso, (8, 256, 256), order='C')

        # Make sure not blank
        self.assertGreater(data_mat_res4_iso.sum(), 1)
        self.assertRaises(AssertionError, np.testing.assert_array_equal, data_mat_res4_aniso, data_mat_res4_iso)

        # Post data, invalidating the downsample operation
        request = factory.post('/' + version + '/cutout/col1/exp_ds_aniso/channel1/0/0:1024/0:1024/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp_ds_aniso', channel='channel1',
                                    resolution='0', x_range='0:1024', y_range='0:1024', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify now NOT downsampled
        request = factory.get('/' + version + '/downsample/col1/exp_ds_aniso/channel1/',
                              content_type='application/json')
        # log in user
        force_authenticate(request, user=self.user)
        response = Downsample.as_view()(request, collection='col1', experiment='exp_ds_aniso',
                                        channel='channel1').render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["num_hierarchy_levels"], 5)
        self.assertEqual(response.data["status"], "NOT_DOWNSAMPLED")

    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        _global_mocked_config_data["aws"]["cuboid_bucket"] = self.object_store_config["cuboid_bucket"]
        _global_mocked_config_data["aws"]["s3-index-table"] = self.object_store_config["s3_index_table"]
        _global_mocked_config_data["aws"]["id-index-table"] = self.object_store_config["id_index_table"]

        # Log Django User in
        self.client.force_login(self.user)

        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        # Populate DB
        self.dbsetup = self.layer.django_setup_helper
        self.dbsetup.insert_iso_data()

    def tearDown(self):
        # Stop mocking
        pass
