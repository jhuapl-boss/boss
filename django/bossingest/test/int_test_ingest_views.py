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

import json
import os
import unittest
from rest_framework.test import APITestCase

import time

from rest_framework.test import APITestCase
from django.conf import settings
from bosscore.test.setup_db import SetupTestDB
from bossingest.test.setup import SetupTests
from bossingest.ingest_manager import IngestManager
from botocore.exceptions import ClientError

from ndingest.ndqueue.ndqueue import NDQueue
from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndqueue.ingestqueue import IngestQueue
from ndingest.ndingestproj.bossingestproj import BossIngestProj

version = settings.BOSS_VERSION


class BossIngestViewTestMixin(object):
    """
    Class to test the ingest services
    """
    def setUp(self):
        """
        Initialize the database
        :return:
        """
        self.client.force_login(self.user)
        NDQueue.test_mode = True

    def tearDown(self):
        NDQueue.test_mode = False

    def test_post_new_ingest_job(self):
        """ Test view to create a new ingest job """
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        assert (upload_queue is not None)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        assert (ingest_queue is not None)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        assert (response.json()['ingest_job']['id'] == ingest_job['id'])
        assert("credentials" in response.json())

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        assert (response.status_code == 204)

        # Verify Queues are removed
        with self.assertRaises(ClientError):
            UploadQueue(nd_proj, endpoint_url=None)
        with self.assertRaises(ClientError):
            IngestQueue(nd_proj, endpoint_url=None)

        # Verify the job is deleted
        url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_not_creator(self):
        """Method to test only creators or admins can interact with ingest jobs"""
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # Log in as the admin and create a job
        self.client.force_login(self.superuser)
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)
        ingest_job = response.json()

        # Log in as the user and try to join but fail
        self.client.force_login(self.user)
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        assert (response.status_code == 403)

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        assert (response.status_code == 403)

    def test_not_creator_admin(self):
        """Method to test only creators or admins can interact with ingest jobs"""
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        assert (upload_queue is not None)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        assert (ingest_queue is not None)

        # Log in as the admin and create a job
        self.client.force_login(self.superuser)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        assert (response.status_code == 200)
        assert (response.json()['ingest_job']['id'] == ingest_job['id'])
        assert("credentials" in response.json())

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        assert (response.status_code == 204)

    def test_list_user_jobs(self):
        """ Test view to create a new ingest job """

        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job_1 = response.json()

        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job_2 = response.json()

        # Delete the job 1
        url = '/' + version + '/ingest/{}/'.format(ingest_job_1['id'])
        response = self.client.delete(url)
        assert (response.status_code == 204)

        # Add a completed job
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)
        ingest_job_completed = response.json()
        url = '/' + version + '/ingest/{}/complete'.format(ingest_job_completed['id'])
        response = self.client.post(url)
        assert(response.status_code == 204)

        # List
        url = '/' + version + '/ingest/'
        response = self.client.get(url, format='json')
        result = response.json()
        self.assertEqual(2, len(result["ingest_jobs"]))
        self.assertEqual(result["ingest_jobs"][0]['id'], ingest_job_2['id'])
        self.assertEqual(result["ingest_jobs"][0]['status'], 0)
        self.assertEqual(result["ingest_jobs"][1]['id'], ingest_job_completed['id'])
        self.assertEqual(result["ingest_jobs"][1]['status'], 2)

    def test_list_admin_jobs(self):
        """ Test listing ALL jobs as the admin user"""
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job_1 = response.json()

        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job_2 = response.json()

        # Delete the job 1
        url = '/' + version + '/ingest/{}/'.format(ingest_job_1['id'])
        response = self.client.delete(url)
        assert (response.status_code == 204)

        # Add a completed job
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)
        ingest_job_completed = response.json()
        url = '/' + version + '/ingest/{}/complete'.format(ingest_job_completed['id'])
        response = self.client.post(url)
        assert(response.status_code == 204)

        # Log in as the admin and create a job
        self.client.force_login(self.superuser)
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        admin_ingest_job = response.json()

        # List
        url = '/' + version + '/ingest/'
        response = self.client.get(url, format='json')
        result = response.json()
        self.assertEqual(3, len(result["ingest_jobs"]))
        self.assertEqual(result["ingest_jobs"][0]['id'], ingest_job_2['id'])
        self.assertEqual(result["ingest_jobs"][0]['status'], 0)
        self.assertEqual(result["ingest_jobs"][1]['id'], ingest_job_completed['id'])
        self.assertEqual(result["ingest_jobs"][1]['status'], 2)
        self.assertEqual(result["ingest_jobs"][2]['id'], admin_ingest_job['id'])
        self.assertEqual(result["ingest_jobs"][2]['status'], 0)

    def test_complete_ingest_job(self):
        """ Test view to create a new ingest job """
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        assert (upload_queue is not None)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        assert (ingest_queue is not None)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        assert(response.json()['ingest_job']['id'] == ingest_job['id'])
        assert("credentials" in response.json())

        # Complete the job
        url = '/' + version + '/ingest/{}/complete'.format(ingest_job['id'])
        response = self.client.post(url)
        assert(response.status_code == 204)

        # Verify Queues are removed
        with self.assertRaises(ClientError):
            UploadQueue(nd_proj, endpoint_url=None)
        with self.assertRaises(ClientError):
            IngestQueue(nd_proj, endpoint_url=None)

        # Verify status has changed
        url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], 2)

    def test_job_status(self):
        """ Test status, waiting for a queue to actually populate """
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(response.status_code, 201)
        ingest_job = response.json()

        # Check status
        url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_message_count"], 640)

        for cnt in range(0, 30):
            # Try joining to kick the status
            url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
            self.client.get(url)

            url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
            response = self.client.get(url)
            if response.json()["status"] == 1:
                break

            time.sleep(10)

        response = self.client.get(url)
        status = response.json()
        self.assertEqual(status["status"], 1)
        self.assertEqual(status["current_message_count"], status["total_message_count"])
        self.assertEqual(status["id"], ingest_job['id'])


class TestIntegrationBossIngestView(BossIngestViewTestMixin, APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Set the environment variable for the tests
        dbsetup = SetupTestDB()
        cls.superuser = dbsetup.create_super_user()
        cls.user = dbsetup.create_user('testuser')
        dbsetup.set_user(cls.user)
        dbsetup.insert_ingest_test_data()

        cls.setup_helper = SetupTests()



