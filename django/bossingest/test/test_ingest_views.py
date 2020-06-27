# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.conf import settings
from bosscore.constants import ADMIN_USER
from bosscore.error import BossError, ErrorCodes
from bossingest.ingest_manager import IngestManager, INGEST_QUEUE_NOT_EMPTY_ERR_MSG
from bossingest.models import IngestJob


version = settings.BOSS_VERSION

@patch('bossingest.views.IngestManager')
class TestBossIngestView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username=ADMIN_USER)

    def test_complete_should_204_when_status_is_complete(self, ingest_mgr_creator):
        job_id = 3
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.COMPLETE
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        ingest_job.creator = testuser
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        actual = self.client.post(url)
        self.assertEqual(204, actual.status_code)

    def test_complete_should_fail_when_status_is_failed(self, ingest_mgr_creator):
        job_id = 2
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.FAILED
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        ingest_job.creator = testuser
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        resp = self.client.post(url, format='json')
        actual = resp.json()
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual['code'])
        self.assertEqual(400, actual['status'])

    def test_complete_should_fail_when_status_is_deleted(self, ingest_mgr_creator):
        job_id = 7
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.DELETED
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        ingest_job.creator = testuser
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        resp = self.client.post(url, format='json')
        self.assertEqual(400, resp.status_code)
        actual = resp.json()
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual['code'])
        self.assertEqual(400, actual['status'])

    def test_complete_should_fail_if_user_not_creator(self, ingest_mgr_creator):
        """
        Only the creator or admin should be able to POST to the complete view.
        This tests a non-admin and non-creator user.
        """
        job_id = 11
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.UPLOADING
        ingest_job.creator = self.admin
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        resp = self.client.post(url, format='json')
        self.assertEqual(403, resp.status_code)
        actual = resp.json()
        self.assertEqual(ErrorCodes.INGEST_NOT_CREATOR, actual['code'])
        self.assertEqual(403, actual['status'])

    def test_complete_should_202_if_ingest_status_is_completing(self, ingest_mgr_creator):
        job_id = 21
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.COMPLETING
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        ingest_job.creator = testuser
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        resp = self.client.post(url, format='json')
        self.assertEqual(202, resp.status_code)

    def test_complete_should_fail_if_queue_not_empty(self, ingest_mgr_creator):
        job_id = 28
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.UPLOADING
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job
        # This method tries to move from UPLOADING to WAIT_ON_QUEUES.
        fake_ingest_mgr.try_enter_wait_on_queue_state.side_effect = BossError(INGEST_QUEUE_NOT_EMPTY_ERR_MSG, ErrorCodes.BAD_REQUEST)

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        ingest_job.creator = testuser
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        resp = self.client.post(url, format='json')
        self.assertEqual(400, resp.status_code)
        actual = resp.json()
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual['code'])
        self.assertEqual(400, actual['status'])

    def test_complete_should_fail_if_wait_on_queues_still_waiting(self, ingest_mgr_creator):
        """Should get a failure response along with how much longer to wait."""
        job_id = 43
        ingest_job = MagicMock(spec=IngestJob)
        ingest_job.status = IngestJob.WAIT_ON_QUEUES
        fake_ingest_mgr = MagicMock(spec=IngestManager)
        fake_ingest_mgr.get_ingest_job.return_value = ingest_job

        wait_remaining = 23

        # This method tries to start the completion process and sets the status.
        fake_ingest_mgr.try_start_completing.return_value = {
            'job_status': IngestJob.WAIT_ON_QUEUES,
            'wait_secs': wait_remaining
        }

        # Provide the fake when the complete view instantiates an IngestManager.
        ingest_mgr_creator.return_value = fake_ingest_mgr

        testuser = User.objects.create_user(username='testuser')
        ingest_job.creator = testuser
        self.client.force_authenticate(user=testuser)

        url = '/{}/ingest/{}/complete'.format(version, job_id)
        resp = self.client.post(url, format='json')
        self.assertEqual(400, resp.status_code)
        actual = resp.json()
        self.assertEqual(IngestJob.WAIT_ON_QUEUES, actual['job_status'])
        self.assertEqual(wait_remaining, actual['wait_secs'])
