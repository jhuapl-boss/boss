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
import unittest
import os

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status

from bossspatialdb.views import Cutout
from bossobject.views import BoundingBox

from bosscore.test.setup_db import SetupTestDB

import numpy as np

from unittest.mock import patch
from mockredis import mock_strict_redis_client


version = settings.BOSS_VERSION


class BoundingBoxMixin(object):

    def test_get_object_bounding_box_single_cuboid(self):
        """ Test getting the bounding box of a object"""

        test_mat = np.ones((128, 128, 16))
        test_mat[0:128, 0:128, 0:16] = 4
        test_mat = test_mat.astype(np.uint64)
        test_mat = test_mat.reshape((16, 128, 128))
        bb = blosc.compress(test_mat, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/1536:1664/1536:1664/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='1536:1664', y_range='1536:1664', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/1536:1664/1536:1664/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='1536:1664', y_range='1536:1664', z_range='0:16', t_range=None).render()
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
        request = factory.get('/' + version + '/boundingbox/col1/exp1/layer1/0/4')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = BoundingBox.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                         resolution='0', id='4')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bb = response.data
        self.assertEqual(bb['t_range'], [0, 1])
        self.assertEqual(bb['x_range'], [1536, 2048])
        self.assertEqual(bb['y_range'], [1536, 2048])
        self.assertEqual(bb['z_range'], [0, 16])

    @unittest.skipUnless(settings.RUN_HIGH_MEM_TESTS, "Test Requires >2.5GB of Memory")
    def test_get_object_bounding_box_span_cuboid_boundary(self):
        """ Test getting the bounding box of a object that spans the z boundary of a cuboid"""

        test_mat = np.ones((516, 516, 18))
        test_mat = test_mat.astype(np.uint64)
        test_mat = test_mat.reshape((18, 516, 516))
        bb = blosc.compress(test_mat, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:516/0:526/0:18/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:516', y_range='0:516', z_range='0:18', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:516/0:516/0:18/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:516', y_range='0:516', z_range='0:18', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (18, 516, 516), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

        # get the bounding box

        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/boundingbox/col1/exp1/layer1/0/1')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = BoundingBox.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                         resolution='0', id='1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bb = response.data
        self.assertEqual(bb['t_range'], [0, 1])
        self.assertEqual(bb['x_range'], [0, 1024])
        self.assertEqual(bb['y_range'], [0, 1024])
        self.assertEqual(bb['z_range'], [0, 32])

    def test_get_object_bounding_box_tight_single_cuboid(self):
        """ Test getting the bounding box of a object"""

        test_mat = np.ones((128, 128, 16))
        test_mat[0:516, 0:516, 0:18] = 3
        test_mat = test_mat.astype(np.uint64)
        test_mat = test_mat.reshape((16, 128, 128))
        bb = blosc.compress(test_mat, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/1024:1152/1024:1152/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='1024:1152', y_range='1024:1152', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/1024:1152/1024:1152/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='1024:1152', y_range='1024:1152', z_range='0:16', t_range=None).render()
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
        request = factory.get('/' + version + '/boundingbox/col1/exp1/layer1/0/3?type=tight')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = BoundingBox.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                         resolution='0', id='3')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bb = response.data
        self.assertEqual(bb['t_range'], [0, 1])
        self.assertEqual(bb['x_range'], [1024, 1152])
        self.assertEqual(bb['y_range'], [1024, 1152])
        self.assertEqual(bb['z_range'], [0, 16])

    @unittest.skipUnless(settings.RUN_HIGH_MEM_TESTS, "Test Requires >2.5GB of Memory")
    def test_get_object_bounding_box_tight_span_cuboid_boundary(self):
        """ Test getting the bounding box of a object that spans the z boundary of a cuboid"""

        test_mat = np.ones((516, 516, 18))
        test_mat[0:516, 0:516, 0:18] = 2
        test_mat = test_mat.astype(np.uint64)
        test_mat = test_mat.reshape((18, 516, 516))
        bb = blosc.compress(test_mat, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:516/0:516/0:18/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:516', y_range='0:516', z_range='0:18', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Create Request to get data you posted
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:516/0:516/0:18/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:516', y_range='0:516', z_range='0:18', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (18, 516, 516), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

        # get the bounding box

        # Create request
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/boundingbox/col1/exp1/layer1/0/2/?type=tight')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = BoundingBox.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                         resolution='0', id='2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        bb = response.data
        self.assertEqual(bb['t_range'], [0, 1])
        self.assertEqual(bb['x_range'], [0, 516])
        self.assertEqual(bb['y_range'], [0, 516])
        self.assertEqual(bb['z_range'], [0, 18])


@patch('redis.StrictRedis', mock_strict_redis_client)
class TestBoundingBoxView(BoundingBoxMixin, APITestCase):

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
