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

import bossutils
import boto3
import json
import os
import unittest
from rest_framework.test import APITestCase
from django.conf import settings
from django.contrib.auth.models import User

from bosscore.test.setup_db import SetupTestDB

version = settings.BOSS_VERSION

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()
testtablename = config["aws"]["meta-db"]


class MetaServiceViewTestsMixin(object):
    """
    The test methods used by both the "unit" level tests and the integration
    level tests.
    """

    def setUp(self):
        """
        Initialize the  database with a some objects to test
        :return:
        """
        """
            Initialize the database
            :return:
            """
        user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(user)

        self.client.force_login(user)
        dbsetup.insert_test_data()

    def test_meta_data_service_collection(self):
        """
        Test to make sure the meta URL for get, post, delete and update with all\
        datamodel params resolves to the meta view
        :return:
        """
        baseurl = '/' + version + '/meta/col1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metadata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 200)

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'][0], 'testmkey')

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 200)

    def test_meta_service_experiment(self):
        """
        Test to make sure the meta URL for get, post, delete and update with an experiment
        :return:
        """
        baseurl = '/' + version + '/meta/col1/exp1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 200)

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'][0], 'testmkey')

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 200)

    def test_meta_service_channel(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/channel1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 200)

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'][0], 'testmkey')

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 200)

    def test_meta_service_layer(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/layer1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection

        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 200)

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'][0], 'testmkey')

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 200)

    def test_meta_service_collection_list(self):
        """
        Test to make sure the meta URL for listing keys for a collection works
        :return:
        """

        baseurl = '/' + version + '/meta/col1/'

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'], [])

    def test_meta_service_experiment_list(self):
        """
        Test meta URL for listing keys for a experiment
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/'

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'], [])

    def test_meta_service_channel_layer_list(self):
        """
        Test meta URL for listing keys for a channel or layer
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/channel1/'

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['keys'], [])

    def test_meta_service_get_invalid(self):
        """
        Test invalid get requests to the meta data service
        :return:
        """

        # data model object does not exist
        baseurl = '/' + version + '/meta/col1/exp1/channel44/'

        # Get all the keys
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 404)

        # key does not exist
        baseurl = '/' + version + '/meta/col1/exp1/channel44/?key=invalid'
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, 404)

    def test_meta_service_post_invalid(self):
        """
        Test invalid post requests to the meta data service
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/layer1/'
        response = self.client.post(baseurl)
        self.assertEqual(response.status_code, 400)

        # post the same key twice
        baseurl = '/' + version + '/meta/col1/exp1/layer1/'
        argspost = '?key=testmkey&value=TestString'
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 400)

    def test_meta_service_delete_invalid(self):
        """
        Test invalid post requests to the meta data service
        """

        baseurl = '/' + version + '/meta/col1/exp1/layer11/'
        argsget = '?key=testmkey'

        # delete the metadata for an invalid object
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 404)

        baseurl = '/' + version + '/meta/col1/exp1/layer1/'

        # delete the metadata without a key
        response = self.client.delete(baseurl)
        self.assertEqual(response.status_code, 400)

        # delete the metadata for a key that does not exist
        response = self.client.delete(baseurl + '?key=test')
        self.assertEqual(response.status_code, 400)

    def test_meta_service_put_invalid(self):
        """
        Test invalid update requests to the meta data service
        """

        baseurl = '/' + version + '/meta/col1/exp1/layer11/'
        argsget = '?key=testmkey'

        # Update the metadata for an invalid object
        response = self.client.put(baseurl + argsget)
        self.assertEqual(response.status_code, 400)

        baseurl = '/' + version + '/meta/col1/exp1/layer1/'

        # Update the metadata without a key
        response = self.client.put(baseurl)
        self.assertEqual(response.status_code, 400)

        # Update the metadata for a key that does not exist
        response = self.client.put(baseurl + '?key=test')
        self.assertEqual(response.status_code, 400)


# Assume there is no local DynamoDB unless the env variable set by jenkins.sh
# present.
@unittest.skipIf(os.environ.get('USING_DJANGO_TESTRUNNER') is None, 'No local DynamoDB.')
class BossCoreMetaServiceViewTests(MetaServiceViewTestsMixin, APITestCase):
    """
    Class to tests the bosscore views for the metadata service
    """
    @classmethod
    def setUpClass(cls):
        # Load table info
        cfgfile = open('bosscore/dynamo_schema.json', 'r')
        tblcfg = json.load(cfgfile)

        # Get table
        session = boto3.Session(aws_access_key_id='foo', aws_secret_access_key='foo')
        dynamodb = session.resource('dynamodb', region_name='us-east-1', endpoint_url='http://localhost:8000')
        cls.table = dynamodb.create_table(
            TableName=testtablename, **tblcfg
        )
        cls.table.meta.client.get_waiter('table_exists').wait(TableName=testtablename)

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        cls.table.meta.client.get_waiter('table_not_exists').wait(TableName=testtablename)
