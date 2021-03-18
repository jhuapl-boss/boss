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

"""
This module tests the ingest completion process of IngestManager.
"""

from unittest.mock import ANY, call, patch, MagicMock
from datetime import datetime, timedelta, timezone

from bossingest.ingest_manager import (
    IngestManager,
    NOT_IN_WAIT_ON_QUEUES_STATE_ERR_MSG,
    UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG,
    INGEST_QUEUE_NOT_EMPTY_ERR_MSG,
    TILE_INDEX_QUEUE_NOT_EMPTY_ERR_MSG,
    TILE_ERROR_QUEUE_NOT_EMPTY_ERR_MSG,
    ALREADY_COMPLETING_ERR_MSG,
    WAIT_FOR_QUEUES_SECS,
    INGEST_LAMBDA,
)
from bossingest.models import IngestJob
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from bosscore.error import BossError, ErrorCodes
from django.contrib.auth.models import User
from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndqueue.ingestqueue import IngestQueue
from ndingest.ndqueue.tileindexqueue import TileIndexQueue
from ndingest.ndqueue.tileerrorqueue import TileErrorQueue
from rest_framework.test import APITestCase

UPLOAD_QUEUE_URL = 'myupload.queue.com'
INGEST_QUEUE_URL = 'myingest.queue.com'
TILE_INDEX_QUEUE_URL = 'mytileindex.queue.com'
TILE_ERROR_QUEUE_URL = 'mytileerror.queue.com'

def make_fake_get_sqs_num_msgs(queue_url_ret_value_list):
    """
    Make a function to use for faking bossingest.utils.get_sqs_num_msgs().

    The returned function can be used with a MagicMock's side_effect.  A
    different integer can be returned for each queue URL.  By default, 0 is
    returned for all known queues.

    Args:
        (list[tuple[str, int]]): A list of url, return value tuples.

    Return:
        (callable): Fake function for replacing get_sqs_num_msgs.
    """
    return_values = {
        UPLOAD_QUEUE_URL: 0,
        INGEST_QUEUE_URL: 0,
        TILE_INDEX_QUEUE_URL: 0,
        TILE_ERROR_QUEUE_URL: 0
    }

    for item in queue_url_ret_value_list:
        return_values[item[0]] = item[1]

    def fake_get_sqs_num_msgs(url, region):
        if url not in return_values:
            raise KeyError('Bad URL given: {}'.format(url))
        return return_values[url]

    return fake_get_sqs_num_msgs


class BossIngestManagerCompleteTest(APITestCase):
    """
    Test the completion process implemented by IngestManager.
    """

    def setUp(self):
        """
        Initialize the database
        """
        # AWS region.
        self.region = 'us-east-1'

        self.user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(self.user)

        self.client.force_login(self.user)
        dbsetup.insert_ingest_test_data()

        SetupTests()

        # Unit under test.
        self.ingest_mgr = IngestManager()

    def patch_ingest_mgr(self, name):
        """
        Patch a method or attribute of self.ingest_manager.

        Allows patching w/o using with so there's not many levels of nested
        indentation.

        Args:
            name (str): Name of method or attribute to replace.

        Returns:
            (MagicMock): Mock or fake
        """
        patch_wrapper = patch.object(self.ingest_mgr, name, autospec=True)
        magic_mock = patch_wrapper.start()
        # This ensures the patch is removed when the test is torn down.
        self.addCleanup(patch_wrapper.stop)
        return magic_mock

    def make_fake_sqs_queues(self):
        """
        Patch the SQS queues used by the ingest manager.
        """
        upload_q = MagicMock(spec=UploadQueue)
        upload_q.url = UPLOAD_QUEUE_URL
        upload_q.region_name = self.region

        get_upload_q = self.patch_ingest_mgr('get_ingest_job_upload_queue')
        get_upload_q.return_value = upload_q

        ingest_q = MagicMock(spec=IngestQueue)
        ingest_q.url = INGEST_QUEUE_URL
        ingest_q.region_name = self.region

        get_ingest_q = self.patch_ingest_mgr('get_ingest_job_ingest_queue')
        get_ingest_q.return_value = ingest_q

        tile_index_q = MagicMock(spec=TileIndexQueue)
        tile_index_q.url = TILE_INDEX_QUEUE_URL
        tile_index_q.region_name = self.region

        get_tile_index_q = self.patch_ingest_mgr('get_ingest_job_tile_index_queue')
        get_tile_index_q.return_value = tile_index_q

        tile_error_q = MagicMock(spec=TileErrorQueue)
        tile_error_q.url = TILE_ERROR_QUEUE_URL
        tile_error_q.region_name = self.region

        get_tile_error_q = self.patch_ingest_mgr('get_ingest_job_tile_error_queue')
        get_tile_error_q.return_value = tile_error_q

    def make_ingest_job(self, **kwargs):
        """
        Create an ingest job for use in a test

        Args:
            kwargs: Keyword args to override the test defaults for the ingest job.

        Returns:
            (IngestJob)
        """
        data = {
            'status': IngestJob.UPLOADING,
            'creator': self.user,
            'resolution': 0,
            'x_start': 0,
            'y_start': 0,
            'z_start': 0,
            't_start': 0,
            'x_stop': 10,
            'y_stop': 10,
            'z_stop': 10,
            't_stop': 1,
            'tile_size_x': 1024,
            'tile_size_y': 1024,
            'tile_size_z': 16,
            'tile_size_t': 1,
            'wait_on_queues_ts': None
        }

        for key, value in kwargs.items():
            data[key] = value

        job = IngestJob.objects.create(**data)
        job.save()
        return job

    @patch('bossingest.ingest_manager.timezone', autospec=True)
    def test_try_enter_wait_on_queue_state_success(self, fake_tz):
        timestamp = datetime.now(timezone.utc)
        fake_tz.now.return_value = timestamp

        job = self.make_ingest_job(status=IngestJob.WAIT_ON_QUEUES, wait_on_queues_ts=timestamp)

        self.patch_ingest_mgr('ensure_queues_empty')
        self.patch_ingest_mgr('_start_completion_activity')
        actual = self.ingest_mgr.try_enter_wait_on_queue_state(job);

        updated_job = self.ingest_mgr.get_ingest_job(job.id)
        self.assertEqual(IngestJob.WAIT_ON_QUEUES, updated_job.status)
        self.assertEqual(timestamp, updated_job.wait_on_queues_ts)

        exp = {
            'job_status': IngestJob.WAIT_ON_QUEUES,
            'wait_secs': WAIT_FOR_QUEUES_SECS
        }
        self.assertDictEqual(exp, actual)

    @patch('bossingest.ingest_manager.timezone', autospec=True)
    def test_try_enter_wait_on_queue_state_already_there(self, fake_tz):
        now_timestamp = datetime.now(timezone.utc)
        fake_tz.now.return_value = now_timestamp

        seconds_waiting = 100
        # Time WAIT_ON_QUEUES entered.
        wait_timestamp = now_timestamp - timedelta(seconds=seconds_waiting)

        job = self.make_ingest_job(status=IngestJob.WAIT_ON_QUEUES, wait_on_queues_ts=wait_timestamp)

        self.patch_ingest_mgr('ensure_queues_empty')
        actual = self.ingest_mgr.try_enter_wait_on_queue_state(job);

        updated_job = self.ingest_mgr.get_ingest_job(job.id)
        self.assertEqual(IngestJob.WAIT_ON_QUEUES, updated_job.status)

        exp = {
            'job_status': IngestJob.WAIT_ON_QUEUES,
            'wait_secs': WAIT_FOR_QUEUES_SECS - seconds_waiting
        }
        self.assertDictEqual(exp, actual)

    def test_try_enter_wait_on_queue_state_should_fail_if_upload_queue_not_empty(self):
        job = self.make_ingest_job(status=IngestJob.UPLOADING)
        fake_ensure_q = self.patch_ingest_mgr('ensure_queues_empty')
        fake_ensure_q.side_effect = BossError(UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG, ErrorCodes.BAD_REQUEST)

        with self.assertRaises(BossError):
            self.ingest_mgr.try_enter_wait_on_queue_state(job)

        updated_job = self.ingest_mgr.get_ingest_job(job.id)
        self.assertEqual(IngestJob.UPLOADING, updated_job.status)

    @patch('bossingest.ingest_manager.timezone', autospec=True)
    def test_try_start_completing_success_case(self, fake_tz):
        now_timestamp = datetime.now(timezone.utc)
        fake_tz.now.return_value = now_timestamp

        seconds_waiting = WAIT_FOR_QUEUES_SECS + 2
        # Time WAIT_ON_QUEUES entered.
        wait_timestamp = now_timestamp - timedelta(seconds=seconds_waiting)

        job = self.make_ingest_job(status=IngestJob.WAIT_ON_QUEUES, wait_on_queues_ts=wait_timestamp)

        self.patch_ingest_mgr('ensure_queues_empty')
        self.patch_ingest_mgr('_start_completion_activity')
        actual = self.ingest_mgr.try_start_completing(job);

        updated_job = self.ingest_mgr.get_ingest_job(job.id)
        self.assertEqual(IngestJob.COMPLETING, updated_job.status)

        exp = {
            'job_status': IngestJob.COMPLETING,
            'wait_secs': 0
        }
        self.assertDictEqual(exp, actual)

    def test_try_start_completing_should_fail_if_not_in_wait_on_queues_state(self):
        """
        This method can only be called when the ingest job status is WAIT_ON_QUEUES.
        """
        job = self.make_ingest_job(status=IngestJob.UPLOADING)

        self.patch_ingest_mgr('ensure_queues_empty')
        self.patch_ingest_mgr('_start_completion_activity')
        with self.assertRaises(BossError) as be:
            self.ingest_mgr.try_start_completing(job);

        actual = be.exception
        self.assertEqual(400, actual.status_code)
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual.error_code)
        self.assertEqual(NOT_IN_WAIT_ON_QUEUES_STATE_ERR_MSG, actual.message)

    def test_try_start_completing_should_return_completing_if_already_completing(self):
        """Should fail if already completing."""
        job = self.make_ingest_job(status=IngestJob.COMPLETING)

        self.patch_ingest_mgr('ensure_queues_empty')
        self.patch_ingest_mgr('_start_completion_activity')
        actual = self.ingest_mgr.try_start_completing(job);
        self.assertEqual(IngestJob.COMPLETING, actual['job_status'])

    @patch('bossingest.ingest_manager.timezone', autospec=True)
    def test_try_start_completing_should_fail_if_queue_wait_period_not_expired(self, fake_tz):
        now_timestamp = datetime.now(timezone.utc)
        fake_tz.now.return_value = now_timestamp

        seconds_waiting = 138
        # Time WAIT_ON_QUEUES entered.
        wait_timestamp = now_timestamp - timedelta(seconds=seconds_waiting)

        job = self.make_ingest_job(status=IngestJob.WAIT_ON_QUEUES, wait_on_queues_ts=wait_timestamp)

        self.patch_ingest_mgr('ensure_queues_empty')
        self.patch_ingest_mgr('_start_completion_activity')
        actual = self.ingest_mgr.try_start_completing(job);

        exp = {
            'job_status': IngestJob.WAIT_ON_QUEUES,
            'wait_secs': WAIT_FOR_QUEUES_SECS - seconds_waiting
        }
        self.assertDictEqual(exp, actual)

    @patch('bossingest.ingest_manager.get_sqs_num_msgs', autospec=True)
    def test_try_start_completing_should_set_uploading_status_on_nonempty_upload_queue(self, fake_get_sqs_num_msgs):
        """If the upload queue isn't empty, the job status should be set to UPLOADING."""
        job = self.make_ingest_job(status=IngestJob.WAIT_ON_QUEUES)

        fake_get_sqs_num_msgs.side_effect = make_fake_get_sqs_num_msgs([(UPLOAD_QUEUE_URL, 1)])
        self.make_fake_sqs_queues()
        self.patch_ingest_mgr('_start_completion_activity')

        with self.assertRaises(BossError) as be:
            self.ingest_mgr.try_start_completing(job);

        actual = be.exception
        self.assertEqual(400, actual.status_code)
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual.error_code)
        self.assertEqual(UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG, actual.message)

        updated_job = self.ingest_mgr.get_ingest_job(job.id)
        self.assertEqual(IngestJob.UPLOADING, updated_job.status)

    @patch('bossingest.ingest_manager.get_sqs_num_msgs', autospec=True)
    def test_ensure_queues_empty_should_fail_if_upload_queue_not_empty(self, fake_get_sqs_num_msgs):
        """Should fail if the upload queue isn't empty."""
        job = self.make_ingest_job(status=IngestJob.UPLOADING)

        fake_get_sqs_num_msgs.side_effect = make_fake_get_sqs_num_msgs([(UPLOAD_QUEUE_URL, 1)])
        self.make_fake_sqs_queues()

        with self.assertRaises(BossError) as be:
            self.ingest_mgr.ensure_queues_empty(job);

        actual = be.exception
        self.assertEqual(400, actual.status_code)
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual.error_code)
        self.assertEqual(UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG, actual.message)

    @patch('bossingest.ingest_manager.get_sqs_num_msgs', autospec=True)
    def test_ensure_queues_empty_should_fail_if_ingest_queue_not_empty(self, fake_get_sqs_num_msgs):
        """Should fail if the ingest queue isn't empty."""
        job = self.make_ingest_job(status=IngestJob.UPLOADING)

        fake_get_sqs_num_msgs.side_effect = make_fake_get_sqs_num_msgs([(INGEST_QUEUE_URL, 1)])
        self.make_fake_sqs_queues()
        self.patch_ingest_mgr('lambda_connect_sqs')

        with self.assertRaises(BossError) as be:
            self.ingest_mgr.ensure_queues_empty(job);

        actual = be.exception
        self.assertEqual(400, actual.status_code)
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual.error_code)
        self.assertEqual(INGEST_QUEUE_NOT_EMPTY_ERR_MSG, actual.message)

    @patch('bossingest.ingest_manager.get_sqs_num_msgs', autospec=True)
    def test_ensure_queues_empty_should_attach_ingest_lambda_if_ingest_queue_not_empty(self, fake_get_sqs_num_msgs):
        """Should fail if the ingest queue isn't empty."""
        job = self.make_ingest_job(status=IngestJob.UPLOADING)

        fake_get_sqs_num_msgs.side_effect = make_fake_get_sqs_num_msgs([(INGEST_QUEUE_URL, 1)])
        self.make_fake_sqs_queues()
        fake_lambda_connect = self.patch_ingest_mgr('lambda_connect_sqs')

        with self.assertRaises(BossError):
            self.ingest_mgr.ensure_queues_empty(job);
        self.assertEquals(fake_lambda_connect.call_args_list, [call(ANY, INGEST_LAMBDA)])

    @patch('bossingest.ingest_manager.get_sqs_num_msgs', autospec=True)
    def test_ensure_queues_empty_should_fail_if_tile_index_queue_not_empty(self, fake_get_sqs_num_msgs):
        """Should fail if the tile index queue isn't empty."""
        job = self.make_ingest_job(status=IngestJob.UPLOADING)

        fake_get_sqs_num_msgs.side_effect = make_fake_get_sqs_num_msgs([(TILE_INDEX_QUEUE_URL, 1)])
        self.make_fake_sqs_queues()

        with self.assertRaises(BossError) as be:
            self.ingest_mgr.ensure_queues_empty(job);

        actual = be.exception
        self.assertEqual(400, actual.status_code)
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual.error_code)
        self.assertEqual(TILE_INDEX_QUEUE_NOT_EMPTY_ERR_MSG, actual.message)

    @patch('bossingest.ingest_manager.get_sqs_num_msgs', autospec=True)
    def test_ensure_queues_empty_should_fail_if_tile_error_queue_not_empty(self, fake_get_sqs_num_msgs):
        """Should fail if the tile error queue isn't empty."""
        job = self.make_ingest_job(status=IngestJob.UPLOADING)

        fake_get_sqs_num_msgs.side_effect = make_fake_get_sqs_num_msgs([(TILE_ERROR_QUEUE_URL, 1)])
        self.make_fake_sqs_queues()

        with self.assertRaises(BossError) as be:
            self.ingest_mgr.ensure_queues_empty(job);

        actual = be.exception
        self.assertEqual(400, actual.status_code)
        self.assertEqual(ErrorCodes.BAD_REQUEST, actual.error_code)
        self.assertEqual(TILE_ERROR_QUEUE_NOT_EMPTY_ERR_MSG, actual.message)

    def test_start_completion_activity_exits_if_not_tile_ingest(self):
        job = self.make_ingest_job(status=IngestJob.UPLOADING)
        job.ingest_type = IngestJob.VOLUMETRIC_INGEST

        self.assertIsNone(self.ingest_mgr._start_completion_activity(job))
