# Copyright 2021 The Johns Hopkins University Applied Physics Laboratory
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

from bosscore.test.setup_db import DjangoSetupLayer
from bosscore.error import BossError

import numpy as np
import zlib
import io
import time
from PIL import Image
from cloudvolume import CloudVolume


# S3 Bucket for CloudVolume Testing.
TEST_BUCKET = "bossdb-test-data"

# bossDB API Version
version = settings.BOSS_VERSION

class CutoutInterfaceViewCloudVolumeMixin(object):
    def test_channel_uint8_cuboid_aligned(self):
        "uint8 - cuboid aligned - no offset"
        
        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint8[0:128, 0:128, 0:16] 

        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/chan1/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='chan1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint8_cuboid_aligned_offset(self):
        "uint8 - cuboid aligned - offset present"

        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint8[0:512, 0:512, 16:32] 
        
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/chan1/0/128:256/256:384/16:32/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='chan1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        offset_mat = test_mat[:, 256:384, 128:256]
        np.testing.assert_array_equal(data_mat, offset_mat)

    def test_channel_uint8_cuboid_unaligned_offset(self):
        "uint8 - cuboid unaligned - offset present"

        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint8[0:1024, 0:512, 0:32] 
        
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T
        
        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/chan1/0/140:692/256:384/7:31/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='chan1',
                                    resolution='0', x_range='140:692', y_range='256:384', z_range='7:31', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (24, 128, 552), order='C')

        # Test for data equality (what you put in is what you got back!)
        offset_mat = test_mat[7:31, 256:384, 140:692]
        np.testing.assert_array_equal(data_mat, offset_mat)
    
    def test_channel_uint16_cuboid_aligned(self):
        "uint16 - cuboid aligned - no offset"
        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint16[0:128, 0:128, 0:16] 
        
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T
        
        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/chan2/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='chan2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint16_cuboid_aligned_offset(self):
        "uint16 - cuboid aligned - offset present"
        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint16[0:512, 0:512, 16:32]
        
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/chan2/0/128:256/256:384/16:32/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='chan2',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        offset_mat = test_mat[:, 256:384, 128:256]
        np.testing.assert_array_equal(data_mat, offset_mat)

    def test_channel_uint16_cuboid_unaligned_offset(self):
        "uint16 - cuboid unaligned - offset present"
        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint16[0:1024, 0:512, 0:32] 
        
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/chan2/0/140:692/256:384/7:31/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='chan2',
                                    resolution='0', x_range='140:692', y_range='256:384', z_range='7:31', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (24, 128, 552), order='C')

        # Test for data equality (what you put in is what you got back!)
        offset_mat = test_mat[7:31, 256:384, 140:692]
        np.testing.assert_array_equal(data_mat, offset_mat)

    def test_channel_uint64_cuboid_aligned(self):
        "uint64 - cuboid aligned - no offset"

        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint64[0:128, 0:128, 0:16]
        
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/anno1/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='anno1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        np.testing.assert_array_equal(data_mat, test_mat)

    def test_channel_uint64_cuboid_aligned_offset(self):
        "uint64 - cuboid aligned - offset present"

        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint64[0:512, 0:512, 16:32]

        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/anno1/0/128:256/256:384/16:32/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='anno1',
                                    resolution='0', x_range='128:256', y_range='256:384', z_range='16:32', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        offset_mat = test_mat[:, 256:384, 128:256]
        np.testing.assert_array_equal(data_mat, offset_mat)

    def test_channel_uint64_cuboid_unaligned_offset(self):
        "uint64 - cuboid unaligned - offset present"

        # Get test data from cloudvolume, returned in XYZT
        test_mat = self.vol_uint64[0:1024, 0:512, 0:32] 
        # Convert to ZYX
        test_mat = np.squeeze(test_mat).T

        # Create Request to get data you posted
        factory = APIRequestFactory()
        request = factory.get('/' + version + '/cutout/col1-cvdb/exp1/anno1/0/140:692/256:384/7:31/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1-cvdb', experiment='exp1', channel='anno1',
                                    resolution='0', x_range='140:692', y_range='256:384', z_range='7:31', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (24, 128, 552), order='C')

        # Test for data equality (what you put in is what you got back!)
        offset_mat = test_mat[7:31, 256:384, 140:692]
        np.testing.assert_array_equal(data_mat, offset_mat)

class TestCutoutCloudVolumeInterfaceView(CutoutInterfaceViewCloudVolumeMixin, APITestCase):
    layer = DjangoSetupLayer
    user = None

    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.user = self.layer.user

    @classmethod
    def setUpClass(cls):
        """ Set everything up for testing """
        # Set up external cloudvolume instance
        # TODO: Fails if cloudvolume not already set up. Make method that creates new cloudvolume.
        cls.vol_uint8 = CloudVolume(f"s3://{TEST_BUCKET}/col1/exp1/chan1", use_https=True)
        cls.vol_uint16 = CloudVolume(f"s3://{TEST_BUCKET}/col1/exp1/chan2", use_https=True)
        cls.vol_uint64 = CloudVolume(f"s3://{TEST_BUCKET}/col1/exp1/anno1", use_https=True)
    
    @classmethod
    def tearDownClass(cls):
        pass