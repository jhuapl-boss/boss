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

from rest_framework.test import APITestCase
from rest_framework.test import force_authenticate
from rest_framework.test import APIRequestFactory

from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth.models import User

from ..request import BossRequest
from bosscore.error import BossError
from .setup_db import SetupTestDB
from bosstiles.views import CutoutTile

version = settings.BOSS_VERSION


class BossTileRequestTests(APITestCase):
    """
    Class to test boss requests
    """

    def setUp(self):
        """
            Initialize the database
            :return:
        """
        self.rf = APIRequestFactory()
        dbsetup = SetupTestDB()
        user = dbsetup.create_super_user(username='testuser', email='test@test.com', password='testuser')
        dbsetup.set_user(user)
        self.user = user
        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_request_tile_init_channel(self):
        """
        Test initialization of tile requests for the datamodel
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/2/0:5/0:6/1/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel1'
        boss_key = 'col1&exp1&channel1'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "1",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version

        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_channel(), channel)
        self.assertEqual(ret.get_boss_key(), boss_key)

    def test_request_tile_init_tileargs_channel(self):
        """
        Test initialization of tile arguments for a tile request
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/2/0:5/0:6/1/'

        res = 2
        (x_start, x_stop) = (0, 5)
        (y_start, y_stop) = (0, 6)
        (z_start, z_stop) = (1, 2)

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "1",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version
        ret = BossRequest(drfrequest, request_args)

        self.assertEqual(ret.get_resolution(), res)
        self.assertEqual(ret.get_x_start(), x_start)
        self.assertEqual(ret.get_x_stop(), x_stop)
        self.assertEqual(ret.get_x_span(), x_stop - x_start)

        self.assertEqual(ret.get_y_start(), y_start)
        self.assertEqual(ret.get_y_stop(), y_stop)
        self.assertEqual(ret.get_y_span(), y_stop - y_start)

        self.assertEqual(ret.get_z_start(), z_start)
        self.assertEqual(ret.get_z_stop(), z_stop)
        self.assertEqual(ret.get_z_span(), z_stop - z_start)

    def test_request_tile_init_tileargs_no_time(self):
        """
        Test initialization of timesample arguments  without a specific timesample
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/2/0:5/0:6/1/'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "1",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version
        ret = BossRequest(drfrequest, request_args)
        time = ret.get_time()
        self.assertEqual(time, range(0, 1))

    def test_request_tile_init_tileargs_time(self):
        """
        Test initialization of timesample arguments  with a single time
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/2/0:5/0:6/1/1/'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 2,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "1",
            "time_args": "1"
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version
        ret = BossRequest(drfrequest, request_args)
        time = ret.get_time()
        self.assertEqual(time, range(1, 2))

    def test_request_tile_invalid_xargs(self):
        """
        Test initialization of tile arguments for a invalid tile request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/0/990:1010/0:6/1/'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 0,
            "x_args": "990:1010",
            "y_args": "0:6",
            "z_args": "1",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_tile_invalid_yargs(self):
        """
        Test initialization of tile arguments for a invalid tile request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/0/0:6/0:1010/1/'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 2,
            "x_args": "0:6",
            "y_args": "0:1010",
            "z_args": "1",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_tile_invalid_zargs(self):
        """
        Test initialization of tile arguments for a invalid tile request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xy/0/0:6/0:6/1040/'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xy",
            "resolution": 0,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "1040",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)

    def test_request_tile_invalid_orientation(self):
        """
        Test initialization of tile arguments for a invalid tile request. The x-args are outside the coordinate
        frame
        :return:
        """
        url = '/' + version + '/image/col1/exp1/channel1/xe/0/0:6/0:6/1/'

        # Create the request dict
        request_args = {
            "service": "image",
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel1",
            "orientation": "xe",
            "resolution": 0,
            "x_args": "0:5",
            "y_args": "0:6",
            "z_args": "1",
            "time_args": None
        }

        # Create the request
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = CutoutTile().initialize_request(request)
        drfrequest.version = version

        with self.assertRaises(BossError):
            BossRequest(drfrequest, request_args)




