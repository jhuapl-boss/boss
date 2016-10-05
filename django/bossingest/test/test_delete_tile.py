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
from __future__ import absolute_import
import os
import unittest
import json
from pkg_resources import resource_filename


from bossingest.ingest_manager import IngestManager
from bossingest.test.setup import SetupTests
from bosscore.test.setup_db import SetupTestDB
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from bosscore.lookup import LookUpKey
from ingest.core.backend import BossBackend
from ndingest.nddynamo.boss_tileindexdb import BossTileIndexDB
from ndingest.ndbucket.tilebucket import TileBucket
import warnings
from ndingest.ndingestproj.bossingestproj import BossIngestProj
from ndingest.settings.settings import Settings
settings = Settings.load()

class BossIngestManagerDeleteTest(APITestCase):

    @classmethod
    def setUpClass(cls):
        # Silence warnings about open boto3 sessions.
        warnings.filterwarnings('ignore')

        cls.job_id = 123
        cls.nd_proj = BossIngestProj('testCol', 'kasthuri11', 'image', 0, cls.job_id)

        TileBucket.createBucket()
        cls.tile_bucket = TileBucket(cls.nd_proj.project_name)

        warnings.simplefilter('ignore')


        #with open('/Users/manavpj1/repos/boss/django/bossingest/test/boss_tile_index.json') as fp:
        #    schema = json.load(fp)

        #BossTileIndexDB.createTable(schema, endpoint_url=settings.DYNAMO_TEST_ENDPOINT)

        cls.tileindex_db = BossTileIndexDB(
            cls.nd_proj.project_name, endpoint_url=settings.DYNAMO_TEST_ENDPOINT)

    @classmethod
    def tearDownClass(cls):
        TileBucket.deleteBucket()

    def setUp(self):
        """
            Initialize the database
            :return:
        """
        self.user = User.objects.create_superuser(username='testuser', email='test@test.com', password='testuser')
        dbsetup = SetupTestDB()
        dbsetup.set_user(self.user)

        self.client.force_login(self.user)
        dbsetup.insert_ingest_test_data()

        # Get the config_data
        config_data = SetupTests().get_ingest_config_data_dict()
        self.example_config_data = config_data


    def test_tile_bucket_name(self):
        """ Test get tile bucket name"""

        ingest_mgmr = IngestManager()
        tile_bucket_name = ingest_mgmr.get_tile_bucket()
        assert(tile_bucket_name is not None)

    def test_upload_tile_index_table(self):
        """"""
        ingest_mgmr = IngestManager()
        ingest_mgmr.validate_config_file(self.example_config_data)
        ingest_mgmr.validate_properties()
        ingest_mgmr.owner = self.user.pk
        ingest_job = ingest_mgmr.create_ingest_job()
        assert (ingest_job.id is not None)

        # Get the chunks in this job
        # Get the project information
        bosskey = ingest_job.collection + '&' + ingest_job.experiment + '&' + ingest_job.channel_layer
        lookup_key = (LookUpKey.get_lookup_key(bosskey)).lookup_key
        [col_id, exp_id, ch_id] = lookup_key.split('&')
        project_info = [col_id, exp_id, ch_id]
        proj_name = ingest_job.collection + '&' + ingest_job.experiment
        tile_index_db = BossTileIndexDB(proj_name)
        tilebucket = TileBucket(str(col_id) + '&' + str(exp_id))

        for time_step in range(ingest_job.t_start, ingest_job.t_stop, 1):
            # For each time step, compute the chunks and tile keys

            for z in range(ingest_job.z_start, ingest_job.z_stop, 16):
                for y in range(ingest_job.y_start, ingest_job.y_stop, ingest_job.tile_size_y):
                    for x in range(ingest_job.x_start, ingest_job.x_stop, ingest_job.tile_size_x):

                        # compute the chunk indices
                        chunk_x = int(x / ingest_job.tile_size_x)
                        chunk_y = int(y / ingest_job.tile_size_y)
                        chunk_z = int(z / 16)

                        # Compute the number of tiles in the chunk
                        if ingest_job.z_stop - z >= 16:
                            num_of_tiles = 16
                        else:
                            num_of_tiles = ingest_job.z_stop - z

                        # Generate the chunk key
                        chunk_key = (BossBackend(ingest_mgmr.config)).encode_chunk_key(num_of_tiles, project_info,
                                                                                       ingest_job.resolution,
                                                                                       chunk_x, chunk_y, chunk_z, time_step)
                        # Upload the chunk to the tile index db
                        tile_index_db.createCuboidEntry(chunk_key, ingest_job.id)
                        key_map = {}
                        for tile in range (0, num_of_tiles):
                            # get the object key and upload it
                            tile_key = tilebucket.encodeObjectKey(ch_id, ingest_job.resolution,
                                                          chunk_x, chunk_y, tile, time_step)
                            tile_key = 'fakekey' + str(tile)
                            tile_index_db.markTileAsUploaded(chunk_key, tile_key)

                        # for each chunk key, delete entries from the tile_bucket


        # Check if data has been uploaded
        chunks = list(tile_index_db.getTaskItems(ingest_job.id))
        assert (len(chunks) != 0)

        ingest_mgmr.delete_tiles(ingest_job)
        chunks = list(tile_index_db.getTaskItems(ingest_job.id))
        assert (len(chunks) == 0)
