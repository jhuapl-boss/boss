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
from rest_framework.test import APITestCase
from django.conf import settings
from bosscore.test.setup_db import SetupTestDB
from bossingest.test.setup import SetupTests
version = settings.BOSS_VERSION


class GroupMemberTests(APITestCase):
    """
    Class to test the manage-data service
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        dbsetup = SetupTestDB()
        user = dbsetup.create_user('testuser')
        dbsetup.set_user(user)
        self.client.force_login(user)
        dbsetup.insert_ingest_test_data()

        self.setup_helper = SetupTests()
        job = self.setup_helper.create_ingest_job()

    def test_get_ingest_job(self):
        """ Test view to join an ingest job """

        # Check if user is a member of the group
        url = '/' + version + '/ingest/1/'
        response = self.client.get(url)
        assert (response.json()['id'] == 1)

    def test_post_new_ingest_job(self):
        """ Test view to create a new ingest job """

        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data= json.loads(json.dumps(config_data))

        # Post the data
        url = '/' + version + '/ingest/'
        response = self.client.post(url,data=config_data, format='json')
        assert (response.status_code == 201)

    def test_delete_ingest_job(self):
        """ Test view to delete an ingest job """

        config_data = self.setup_helper.get_ingest_config_data_dict()
        config_data = json.loads(json.dumps(config_data))

        # Post the job
        url = '/' + version + '/ingest/'
        response = self.client.post(url, data=config_data, format='json')
        assert (response.status_code == 201)
        job_id = response.json()['id']

        # Delete the job
        url = '/' + version + '/ingest/{}/'.format(job_id)
        response = self.client.delete(url)
        assert (response.status_code == 204)

