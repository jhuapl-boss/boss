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
This file tests a function that writes to the DB on the activity server.
Because Django owns the DB, it makes sense for the test to live here, rather
than in the boss-tools repo.

Tests run on the endpoint server will not have the activities module, so the
tests will be skipped if the module cannot be imported.
"""

try:
    from activities.boss_db import update_downsample_status_in_db
    HAVE_ACTIVITIES_MODULE = True
except Exception:
    HAVE_ACTIVITIES_MODULE = False

from bosscore.models import Channel, Collection, CoordinateFrame, Experiment
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TransactionTestCase
import pymysql.cursors
from unittest import skipIf
from unittest.mock import patch


@skipIf(not HAVE_ACTIVITIES_MODULE, 'activities module not present')
class TestUpdateDownsampleStatus(TransactionTestCase):
    def setUp(self):
        user = User.objects.create_user(username='testuser')
        cf = CoordinateFrame(name='frame', creator=user,
                             x_start=0, x_stop=100, y_start=0, y_stop=100, z_start=0, z_stop=100,
                             x_voxel_size=10, y_voxel_size=10, z_voxel_size=10,
                             voxel_unit='nanometers')
        cf.save()
        col = Collection.objects.create(name='col', creator=user)
        col.save()
        exp = Experiment.objects.create(name='exp', collection=col, creator=user, coord_frame=cf)
        exp.save()
        chan = Channel.objects.create(name='chan', experiment=exp, creator=user, type='image', datatype='uint8')
        chan.save()

        self.chan_id = chan.id
        self.setup_db_conn_mock()

    def setup_db_conn_mock(self):
        patch_wrapper = patch('activities.boss_db.get_db_connection', autospec=True)
        mock_get_db_conn = patch_wrapper.start()
        db = settings.DATABASES['default']
        mock_get_db_conn.return_value = pymysql.connect(
            host=db['HOST'],
            user=db['USER'],
            password=db['PASSWORD'],
            db=db['NAME'],
            port=db['PORT'],
            autocommit=True,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor)
        self.addCleanup(patch_wrapper.stop)

    def test_set_in_progress(self):
        args = {
            'db_host': 'localhost',
            'channel_id': self.chan_id,
            'status': Channel.DownsampleStatus.IN_PROGRESS
        }
        actual = update_downsample_status_in_db(args)

        # Should return whatever the input args were so they can be passed to
        # the next step function state.
        self.assertDictEqual(args, actual)

        chan = Channel.objects.get(id=self.chan_id)
        self.assertEqual(Channel.DownsampleStatus.IN_PROGRESS, chan.downsample_status)

    def test_set_downsampled(self):
        args = {
            'db_host': 'localhost',
            'channel_id': self.chan_id,
            'status': Channel.DownsampleStatus.DOWNSAMPLED
        }
        actual = update_downsample_status_in_db(args)

        # Should return whatever the input args were so they can be passed to
        # the next step function state.
        self.assertDictEqual(args, actual)

        chan = Channel.objects.get(id=self.chan_id)
        self.assertEqual(Channel.DownsampleStatus.DOWNSAMPLED, chan.downsample_status)
