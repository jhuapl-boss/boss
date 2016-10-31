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
from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from django.conf import settings

from bosscore.request import BossRequest
from bosscore.test.setup_db import SetupTestDB
from bossmeta.views import BossMeta
from bosscore.error import BossError

version = settings.BOSS_VERSION


class BossCoreMetaValidRequestTests(APITestCase):
    """
    Class to test Meta data requests
    """

    def setUp(self):
        """
        Initialize the test database with some objects
        :return:
        """
        self.rf = APIRequestFactory()
        dbsetup = SetupTestDB()
        self.user = dbsetup.create_user('testuser')
        dbsetup.set_user(self.user)

        self.client.force_login(self.user)
        dbsetup.insert_test_data()

    def test_collection_init(self):
        """
        Test initialization of requests from the meta data service with collection
        :return:
        """
        # create the request with collection name
        # log in user


        url = '/' + version + '/meta/col1/?key=mkey&value=TestValue'
        expected_col = 'col1'
        expected_bosskey = 'col1'
        expected_key = 'mkey'
        expected_value = 'TestValue'

        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": expected_col,
            "experiment_name": None,
            "channel_name": None,
            "key": "mkey",
            "value": "TestValue"
        }

        # Datamodel object
        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(ret.get_collection(), expected_col)

        # Boss key
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key, expected_bosskey)

        # Key and value
        key = ret.get_key()
        self.assertEqual(key, expected_key)
        value = ret.get_value()
        self.assertEqual(value, expected_value)

    def test_collection_special_char_dash(self):
        """
        Test initialization of requests from the meta data service with collection that has a dash in the name
        :return:
        """
        # create the request with collection name
        # log in user


        url = '/' + version + '/meta/col1-22/?key=mkey&value=TestValue'
        expected_col = 'col1-22'
        expected_bosskey = 'col1-22'
        expected_key = 'mkey'
        expected_value = 'TestValue'

        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": expected_col,
            "experiment_name": None,
            "channel_name": None,
            "key": "mkey",
            "value": "TestValue"
        }

        # Datamodel object
        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(ret.get_collection(), expected_col)

        # Boss key
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key, expected_bosskey)

        # Key and value
        key = ret.get_key()
        self.assertEqual(key, expected_key)
        value = ret.get_value()
        self.assertEqual(value, expected_value)

    def test_experiment_init(self):
        """
        Test initialization of requests from the meta data service with valid collection and experiment
        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/?key=mkey&value=TestValue'
        expected_col = 'col1'
        expected_exp = 'exp1'
        expected_bosskey = 'col1&exp1'
        expected_key = 'mkey'
        expected_value = 'TestValue'
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": expected_col,
            "experiment_name": expected_exp,
            "channel_name": None,
            "key": "mkey",
            "value": "TestValue"
        }

        ret = BossRequest(drfrequest, request_args)

        # Datamodel object
        self.assertEqual(ret.get_collection(), expected_col)
        self.assertEqual(ret.get_experiment(), expected_exp)

        # Boss key
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key, expected_bosskey)

        # Key and value
        key = ret.get_key()
        self.assertEqual(key, expected_key)
        value = ret.get_value()
        self.assertEqual(value, expected_value)

    def test_bossrequest_init_channel(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment and channel

        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/channel1/?key=mkey&value=TestValue'
        expected_col = 'col1'
        expected_exp = 'exp1'
        expected_channel = 'channel1'
        expected_bosskey = 'col1&exp1&channel1'
        expected_key = 'mkey'
        expected_value = 'TestValue'

        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": expected_col,
            "experiment_name": expected_exp,
            "channel_name": expected_channel,
            "key": "mkey",
            "value": "TestValue"
        }

        # Data model Objects
        ret = BossRequest(drfrequest, request_args)
        self.assertEqual(ret.get_collection(), expected_col)
        self.assertEqual(ret.get_experiment(), expected_exp)
        self.assertEqual(ret.get_channel(), expected_channel)

        # Boss key
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key, expected_bosskey)

        # Key and value
        key = ret.get_key()
        self.assertEqual(key, expected_key)
        value = ret.get_value()
        self.assertEqual(value, expected_value)


    def test_bossrequest_init_coordinateframe(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment and dataset
        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/channel1/?key=mkey'
        expected_col = 'col1'
        expected_exp = 'exp1'
        expected_channel = 'channel1'
        expected_coord = 'cf1'
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": expected_col,
            "experiment_name": expected_exp,
            "channel_name": expected_channel,
            "key": "mkey",
        }
        ret = BossRequest(drfrequest, request_args)

        # Data model objects
        self.assertEqual(ret.get_collection(), expected_col)
        self.assertEqual(ret.get_experiment(), expected_exp)
        self.assertEqual(ret.get_channel(), expected_channel)

        # Check coordinate frame
        self.assertEqual(ret.get_coordinate_frame(), expected_coord)

    def test_bossrequest_list_all_keys(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment and channel
        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/channel1/'
        expected_col = 'col1'
        expected_exp = 'exp1'
        expected_channel = 'channel1'
        expected_coord = 'cf1'
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": expected_col,
            "experiment_name": expected_exp,
            "channel_name": expected_channel,
            "key": None,
            "value": None
        }

        ret = BossRequest(drfrequest, request_args)

        # Data model objects
        self.assertEqual(ret.get_collection(), expected_col)
        self.assertEqual(ret.get_experiment(), expected_exp)
        self.assertEqual(ret.get_channel(), expected_channel)

        # Key and value should be empty
        self.assertEqual(ret.get_key(), None)
        self.assertEqual(ret.get_value(), None)


class BossCoreMetaInvalidRequestTests(APITestCase):
    """
    Class to test invalid requests for the meta data service
    """

    def setUp(self):
        """
        Initialize the test database with some objects
        :return:
        """
        self.rf = APIRequestFactory()

        dbsetup = SetupTestDB()
        self.user = dbsetup.create_user('testuser')
        dbsetup.set_user(self.user)

        self.client.force_login(self.user)
        dbsetup.insert_test_data()

    def test_bossrequest_collection_not_found(self):
        """
        Test initialization of requests with a collection that does not exist

        """
        # create the request
        url = '/' + version + '/meta/col2/?key=mkey'
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        try:
            # Create the request dict
            request_args = {
                "user": self.user,
                "method": request.method,
                "service": "meta",
                "version": version,
                "collection_name": "col2",
                "experiment_name": None,
                "channel_name": None,
                "key": "mkey",
                "value": None
            }
            BossRequest(drfrequest, request_args)
        except BossError as err:
            assert err.status_code == 404

    def test_bossrequest_experiment_not_found(self):
        """
        Test initialization of requests with a experiment that does not exist

        """
        # create the request
        url = '/' + version + '/meta/col1/exp2/?key=mkey'
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        try:
            # Create the request dict
            request_args = {
                "user": self.user,
                "method": request.method,
                "service": "meta",
                "version": version,
                "collection_name": "col1",
                "experiment_name": None,
                "channel_name": None,
                "key": "mkey",
                "value": None
            }
            BossRequest(drfrequest, request_args)
        except BossError as err:
            assert err.status_code == 404

    def test_bossrequest_channel_not_found(self):
        """
        Test initialization of requests with a channel that does not exist

        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/channel2/?key=mkey'
        request = self.rf.get(url)
        force_authenticate(request, user=self.user)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        # Create the request dict
        request_args = {
            "user": self.user,
            "method": request.method,
            "service": "meta",
            "version": version,
            "collection_name": "col1",
            "experiment_name": "exp1",
            "channel_name": "channel2",
            "key": "mkey",
            "value": None
        }

        try:
            BossRequest(drfrequest,request_args)
        except BossError as err:
            assert err.args[0] == 404
