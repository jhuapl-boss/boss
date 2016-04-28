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
from rest_framework.request import Request
from django.http import HttpRequest
from django.conf import settings
from django.contrib.auth.models import User

from ..request import BossRequest
from .setup_db import SetupTestDB

version = settings.BOSS_VERSION


class BossCoreRequestTests(APITestCase):
    """
    Class to test boss requests
    """

    def setUp(self):
        """
            Initialize the database
            :return:
        """
        user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_request_cutout_init_channel(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel1'
        boss_key = 'col1&exp1&channel1'
        boss_key_list = 'col1&exp1&channel1&2&0'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_channel_layer(), channel)
        self.assertEqual(ret.get_boss_key(), boss_key)
        self.assertEqual(ret.get_boss_key_list()[0], boss_key_list)

    def test_request_cutout_init_layer(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/layer1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        layer = 'layer1'
        boss_key = 'col1&exp1&layer1&2&0'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_channel_layer(), layer)
        self.assertEqual(ret.get_boss_key_list()[0], boss_key)

    def test_request_cutout_init_cutoutargs_channel(self):
        """
        Test initialization of cutout arguments for a cutout request
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'

        res = 2
        (x_start, x_stop) = (0, 5)
        (y_start, y_stop) = (0, 6)
        (z_start, z_stop) = (0, 2)

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)

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

    def test_request_cutout_init_cutoutargs_no_time(self):
        """
        Test initialization of timesample arguments  without a specific timesample
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        time = ret.get_time()
        self.assertEqual(time, range(0, 1))

    def test_request_cutout_init_cutoutargs_time(self):
        """
        Test initialization of timesample arguments  with a single time
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1/'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        time = ret.get_time()
        self.assertEqual(time, range(1, 2))

    def test_request_cutout_init_cutoutargs_time_range(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1:5/'
        exp_boss_keys = ['col1&exp1&channel1&2&1',
                         'col1&exp1&channel1&2&2',
                         'col1&exp1&channel1&2&3',
                         'col1&exp1&channel1&2&4']

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        time = ret.get_time()
        boss_keys = ret.get_boss_key_list()
        self.assertEqual(time, range(1, 5))
        self.assertEqual(boss_keys, exp_boss_keys)

    def test_request_cutout_bosskey_time(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1:5/'
        exp_boss_keys = ['col1&exp1&channel1&2&1',
                         'col1&exp1&channel1&2&2',
                         'col1&exp1&channel1&2&3',
                         'col1&exp1&channel1&2&4']

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        boss_keys = ret.get_boss_key_list()
        self.assertEqual(boss_keys, exp_boss_keys)

        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/1:2/'
        exp_boss_keys = ['col1&exp1&channel1&2&0']

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        boss_keys = ret.get_boss_key_list()
        self.assertEqual(boss_keys, exp_boss_keys)

        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1/'
        exp_boss_keys = ['col1&exp1&channel1&2&1']

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        boss_keys = ret.get_boss_key_list()
        self.assertEqual(boss_keys, exp_boss_keys)

    def test_request_cutout_lookupkey(self):
        """
        Test initialization of boss_key for a time sample range
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/1:5/'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        col_id = ret.collection.pk
        exp_id = ret.experiment.pk
        channel_layer_id = ret.channel_layer.pk
        base_lookup = str(col_id) + '&' + str(exp_id) + '&' + str(channel_layer_id)
        exp_lookup_keys = []
        exp_lookup_keys.append(base_lookup+'&2&1')
        exp_lookup_keys.append(base_lookup+'&2&2')
        exp_lookup_keys.append(base_lookup+'&2&3')
        exp_lookup_keys.append(base_lookup+'&2&4')

        lookup_keys = ret.get_lookup_key_list()
        self.assertEqual(base_lookup, ret.get_lookup_key())
        self.assertEqual(lookup_keys, exp_lookup_keys)
