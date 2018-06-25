from bossingest.utils import query_tile_index, _query_tile_index, _create_messages
from ingestclient.core.backend import BossBackend
import json
import os
from tempfile import NamedTemporaryFile
import unittest
from unittest.mock import patch

def fake_query_nonempty_data(job_id):
    return [
        {'Items': [
            {
                'chunk_key': {'S': 'some_chunk_key' },
                'task_id': {'N': job_id},
                'tile_uploaded_map': { 'M': {
                    'fakekey1': 1,
                    'fakekey2': 1,
                    'fakekey3': 1,
                    'fakekey4': 1,
                    'fakekey5': 1,
                    'fakekey6': 1,
                    'fakekey7': 1,
                    'fakekey8': 1,
                    'fakekey9': 1,
                    'fakekey10': 1,
                    'fakekey11': 1,
                    'fakekey12': 1,
                    'fakekey13': 1,
                    'fakekey14': 1,
                    'fakekey15': 1,
                    'fakekey16': 1
                } }
            },
            {
                'chunk_key': {'S': 'some_chunk_key2' },
                'task_id': {'N': job_id},
                'tile_uploaded_map': { 'M': {
                    'fakekey21': 1,
                    'fakekey22': 1,
                    'fakekey23': 1,
                    'fakekey24': 1,
                    'fakekey25': 1,
                    'fakekey26': 1,
                    'fakekey27': 1,
                    'fakekey28': 1,
                    'fakekey29': 1,
                    'fakekey30': 1,
                    'fakekey31': 1,
                    'fakekey32': 1,
                    'fakekey33': 1,
                    'fakekey34': 1,
                    'fakekey35': 1,
                    'fakekey36': 1
                } } 
            }
        ]}
    ]

def fake_query_tile_ind_side_effects(paginator, tile_index_name, job_id, i):
    if i != 20:
        return []

    return fake_query_nonempty_data(job_id)


class TestUtils(unittest.TestCase):

    @patch('bossingest.utils._query_tile_index', return_value=[])
    def test_query_tile_index_no_chunks(self, fake_query_tile_ind):
        job_id = 4
        tile_index_name = 'tiles.test.boss'
        region = 'us-east-1'
        self.assertIsNone(query_tile_index(job_id, tile_index_name, region))

    @patch('bossingest.utils._query_tile_index', side_effect=fake_query_tile_ind_side_effects)
    def test_query_tile_index(self, fake_query_tile_ind):
        job_id = 4
        tile_index_name = 'tiles.test.boss'
        region = 'us-east-1'
        csv_file = query_tile_index(job_id, tile_index_name, region)
        expected = fake_query_nonempty_data(job_id)

        try:
            with open(csv_file, 'rt') as csv_in:
                lines = csv_in.readlines()
                for i, line in enumerate(lines):
                    columns = line.strip().split(',')
                    if i < 2:
                        exp = expected[0]['Items'][i]
                        self.assertEqual(exp['chunk_key']['S'], columns[0])
                        self.assertEqual(exp['task_id']['N'], int(columns[1]))
                        self.assertEqual(len(exp['tile_uploaded_map']['M']), int(columns[2]))
                    else:
                        self.fail('Too many lines written')
        finally:
            os.remove(csv_file)

    def test_create_messages(self):
        job_id = 8
        num_tiles = 16
        exp_upload_queue = 'upload-test-queue'
        exp_ingest_queue = 'ingest-test-queue'
        args = {
            'job_id': job_id,
            'project_info': [5, 3, 2], # Collection/Experiment/Channel ids
            'z_chunk_size': 16,
            'resolution': 0,
            'upload_queue': exp_upload_queue,
            'ingest_queue': exp_ingest_queue
        }

        backend = BossBackend(None)
        x1, y1, z1 = (0, 0, 0)
        x2, y2, z2  = (1024, 1024, 16)
        res = 0
        t = 2
        chunk_key1 = backend.encode_chunk_key(num_tiles, args['project_info'], res, x1, y1, z1, t) 
        chunk_key2 = backend.encode_chunk_key(num_tiles, args['project_info'], res, x2, y2, z2, t)
        with NamedTemporaryFile(
            mode='wt',
            suffix='.csv',
            delete=False
        ) as output_csv:
            csv_file = output_csv.name
            output_csv.write('{},{},{}'.format(chunk_key1, job_id, num_tiles))
            output_csv.write('{},{},{}'.format(chunk_key2, job_id, num_tiles))

        try:
            actual = _create_messages(args, csv_file)
            for i, raw_msg in enumerate(actual):
                msg = json.loads(raw_msg)
                self.assertEqual(job_id, msg['job_id'])
                self.assertEqual(exp_upload_queue, msg['upload_queue_arn'])
                self.assertEqual(exp_ingest_queue, msg['ingest_queue_arn'])
                if i < 16:
                    self.assertEqual(chunk_key1, msg['chunk_key'])
                    exp_tile_key = backend.encode_tile_key(
                        args['project_info'], res, x1, y1, z1 + i, t)
                    self.assertEqual(exp_tile_key, msg['tile_key'])
                elif i < 32:
                    self.assertEqual(chunk_key2, msg['chunk_key'])
                    exp_tile_key = backend.encode_tile_key(
                        args['project_info'], res, x2, y2, z2 + i - 16, t)
                    self.assertEqual(exp_tile_key, msg['tile_key'])
                else:
                    self.fail('Too many messages returned')

        finally:
            os.remove(csv_file)

