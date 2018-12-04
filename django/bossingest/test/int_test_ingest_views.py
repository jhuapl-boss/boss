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
from bossingest.models import IngestJob
from botocore.exceptions import ClientError

from contextlib import contextmanager

from ndingest.nddynamo.boss_tileindexdb import BossTileIndexDB
from ndingest.ndqueue.ndqueue import NDQueue
from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndqueue.ingestqueue import IngestQueue
from ndingest.ndingestproj.bossingestproj import BossIngestProj

from random import randint;

version = settings.BOSS_VERSION

@contextmanager
def add_tile_entry(ingest_job):
    """
    Put a fake chunk in the tile index for the given job.  Cleans up fake chunk
    when it goes out of scope.

    Args:
        ingest_job (dict): Job data as returned by the POST method.

    Yields:
        (None)
    """
    tiledb = BossTileIndexDB(ingest_job['collection'] + '&' + ingest_job['experiment'])
    chunk_key = '{}&16&1&2&3&0&0&0&0&0'.format(randint(0, 2000))
    tiledb.createCuboidEntry(chunk_key, ingest_job['id'])
    # Mark some tiles as uploaded.
    for i in range(12):
        tiledb.markTileAsUploaded(chunk_key, 'fake_tile_key_{}'.format(i), ingest_job['id'])
    yield

    # Cleanup.
    print('deleting fake chunk')
    tiledb.deleteCuboid(chunk_key, ingest_job['id'])


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
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(upload_queue)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(ingest_queue)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.json()['ingest_job']['id'], ingest_job['id'])
        self.assertIn("credentials", response.json())

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        self.assertEqual(204, response.status_code)

        # Verify Queues are removed
        with self.assertRaises(ClientError):
            UploadQueue(nd_proj, endpoint_url=None)
        with self.assertRaises(ClientError):
            IngestQueue(nd_proj, endpoint_url=None)

        # Verify the job is deleted
        url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_new_volumetric_ingest_job(self):
        """ Test view to create a new volumetric_ingest job """
        config_data = self.setup_helper.get_ingest_config_data_dict_volumetric()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(upload_queue)

        # There shouldn't be an ingest queue for a volumetric ingest
        with self.assertRaises(ClientError):
            IngestQueue(nd_proj, endpoint_url=None)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.json()['ingest_job']['id'], ingest_job['id'])
        self.assertIn("credentials", response.json())

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        self.assertEqual(204, response.status_code)

        # Verify Queues are removed
        with self.assertRaises(ClientError):
            UploadQueue(nd_proj, endpoint_url=None)

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
        self.assertEqual(201, response.status_code)
        ingest_job = response.json()

        # Log in as the user and try to join but fail
        self.client.force_login(self.user)
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        self.assertEqual(403, response.status_code)

    def test_not_creator_admin(self):
        """Method to test only creators or admins can interact with ingest jobs"""
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(upload_queue)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(ingest_queue)

        # Log in as the admin and create a job
        self.client.force_login(self.superuser)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json()['ingest_job']['id'], ingest_job['id'])
        self.assertIn("credentials", response.json())

        # # Delete the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.delete(url)
        self.assertEqual(204, response.status_code)

    def test_list_user_jobs(self):
        """ Test view to create a new ingest job """

        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job_1 = response.json()

        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job_2 = response.json()

        # Delete the job 1
        url = '/' + version + '/ingest/{}/'.format(ingest_job_1['id'])
        response = self.client.delete(url)
        self.assertEqual(204, response.status_code)

        # Add another job
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)
        ingest_job_3 = response.json()

        # List
        url = '/' + version + '/ingest/'
        response = self.client.get(url, format='json')
        result = response.json()
        self.assertEqual(2, len(result["ingest_jobs"]))
        self.assertEqual(result["ingest_jobs"][0]['id'], ingest_job_2['id'])
        self.assertEqual(result["ingest_jobs"][0]['status'], 0)
        self.assertEqual(result["ingest_jobs"][1]['id'], ingest_job_3['id'])
        self.assertEqual(result["ingest_jobs"][1]['status'], 0)

    def test_list_admin_jobs(self):
        """ Test listing ALL jobs as the admin user"""
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job_1 = response.json()

        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        ingest_job_2 = response.json()

        # Delete the job 1
        url = '/' + version + '/ingest/{}/'.format(ingest_job_1['id'])
        response = self.client.delete(url)
        self.assertEqual(204, response.status_code)

        # Add a job that will be completed
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)
        ingest_job_completed = response.json()

        # Wait for job to "complete"
        for cnt in range(0, 30):
            # Try joining to kick the status
            url = '/' + version + '/ingest/{}/'.format(ingest_job_completed['id'])
            self.client.get(url)

            url = '/' + version + '/ingest/{}/status'.format(ingest_job_completed['id'])
            response = self.client.get(url)
            if response.json()["status"] == IngestJob.UPLOADING:
                break

            time.sleep(10)

        # Complete the job
        url = '/' + version + '/ingest/{}/complete'.format(ingest_job_completed['id'])
        response = self.client.post(url)
        self.assertEqual(204, response.status_code)

        # Log in as the admin and create a job
        self.client.force_login(self.superuser)
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(201, response.status_code)

        # Check if the queue's exist
        admin_ingest_job = response.json()

        # List
        url = '/' + version + '/ingest/'
        response = self.client.get(url, format='json')
        result = response.json()
        self.assertEqual(3, len(result["ingest_jobs"]))
        self.assertEqual(result["ingest_jobs"][0]['id'], ingest_job_2['id'])
        self.assertEqual(result["ingest_jobs"][0]['status'], IngestJob.PREPARING)
        self.assertEqual(result["ingest_jobs"][1]['id'], ingest_job_completed['id'])
        self.assertEqual(result["ingest_jobs"][1]['status'], IngestJob.COMPLETE)
        self.assertEqual(result["ingest_jobs"][2]['id'], admin_ingest_job['id'])
        self.assertEqual(result["ingest_jobs"][2]['status'], IngestJob.PREPARING)

    def test_complete_ingest_job(self):
        """ Test view to create a new ingest job """
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(response.status_code, 201)

        # Check if the queues exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(upload_queue)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(ingest_queue)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.json()['ingest_job']['id'], ingest_job['id'])
        self.assertIn("credentials", response.json())

        # Complete the job
        url = '/' + version + '/ingest/{}/complete'.format(ingest_job['id'])
        response = self.client.post(url)

        # Can't complete until it is done
        self.assertEqual(400, response.status_code)

        # Wait for job to complete
        print('trying to join job')
        for cnt in range(0, 30):
            # Try joining to kick the status
            url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
            self.client.get(url)

            url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
            response = self.client.get(url)
            if response.json()["status"] == IngestJob.UPLOADING:
                break

            time.sleep(10)

        print('completing')
        # Complete the job
        url = '/' + version + '/ingest/{}/complete'.format(ingest_job['id'])
        response = self.client.post(url)
        self.assertEqual(204, response.status_code)

        # Verify Queues are removed
        with self.assertRaises(ClientError):
            UploadQueue(nd_proj, endpoint_url=None)
        with self.assertRaises(ClientError):
            IngestQueue(nd_proj, endpoint_url=None)

        # Verify status has changed
        url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json()["status"], 2)

    def test_verify_ingest_job_not_done(self):
        """ Test view to create a new ingest job """
        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        self.assertEqual(response.status_code, 201)

        # Check if the queue's exist
        ingest_job = response.json()
        proj_class = BossIngestProj.load()
        nd_proj = proj_class(ingest_job['collection'], ingest_job['experiment'], ingest_job['channel'],
                             0, ingest_job['id'])
        self.nd_proj = nd_proj
        upload_queue = UploadQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(upload_queue)
        ingest_queue = IngestQueue(nd_proj, endpoint_url=None)
        self.assertIsNotNone(ingest_queue)

        # Test joining the job
        url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
        response = self.client.get(url)
        self.assertEqual(response.json()['ingest_job']['id'], ingest_job['id'])
        self.assertIn("credentials", response.json())

        # Wait for job to complete
        print('trying to join job')
        for cnt in range(0, 30):
            # Try joining to kick the status
            url = '/' + version + '/ingest/{}/'.format(ingest_job['id'])
            self.client.get(url)

            url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
            response = self.client.get(url)
            if response.json()["status"] == IngestJob.UPLOADING:
                break

            time.sleep(10)

        print('faking ingest')
        # Leave one chunk in the index to fake not being done.
        with add_tile_entry(ingest_job):
            print('trying to complete')
            url = '/' + version + '/ingest/{}/complete'.format(ingest_job['id'])
            response = self.client.post(url)
            # Still have chunks in tile index
            self.assertEqual(202, response.status_code)

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
            if response.json()["status"] == IngestJob.UPLOADING:
                break

            time.sleep(10)

        url = '/' + version + '/ingest/{}/status'.format(ingest_job['id'])
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



