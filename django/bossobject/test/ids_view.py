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
from bossobject.views import Ids

from bosscore.test.setup_db import SetupTestDB

import numpy as np

from unittest.mock import patch
from fakeredis import FakeStrictRedis


version = settings.BOSS_VERSION


class IdsMixin(object):

    def test_channel_uint64_cuboid_aligned_no_offset_no_time_blosc(self):
        """ Test uint64 data, cuboid aligned, no offset, no time samples"""

        test_mat = np.ones((128, 128, 16))
        test_mat = test_mat.astype(np.uint64)
        test_mat = test_mat.reshape((16, 128, 128))
        bb = blosc.compress(test_mat, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

        # get the bounding box

        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/ids/col1/exp1/layer1/0/0:128/0:128/0:16/')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Ids.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                         resolution='0', x_range='0:128', y_range='0:128', z_range='0:16',
                                         t_range=None)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ids'], ['1'])


@patch('redis.StrictRedis', FakeStrictRedis)
class TestCutoutInterfaceView(IdsMixin, APITestCase):

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

