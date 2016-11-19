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

from pkg_resources import resource_filename
import json

from bossutils.aws import get_region

from moto import mock_s3
from moto import mock_dynamodb2
from moto import mock_sqs
import boto3
from botocore.exceptions import ClientError

import time
from spdb.project.test.resource_setup import get_image_dict
from spdb.project import BossResourceBasic

from bossutils import configuration

import random


class SetupTests(object):
    """ Class to handle setting up tests, including support for mocking
    """
    def __init__(self):
        self.mock = True
        self.mock_s3 = None
        self.mock_dynamodb = None
        self.mock_sqs = None

        self.DYNAMODB_SCHEMA = resource_filename('spdb', 'spatialdb/dynamo/s3_index_table.json')
        self.ID_INDEX_SCHEMA = resource_filename('spdb', 'spatialdb/dynamo/id_index_schema.json')
        self.ID_COUNT_SCHEMA = resource_filename('spdb', 'spatialdb/dynamo/id_count_schema.json')

    def start_mocking(self):
        """Method to start mocking"""
        self.mock = True
        self.mock_s3 = mock_s3()
        self.mock_dynamodb = mock_dynamodb2()
        self.mock_sqs = mock_sqs()
        self.mock_s3.start()
        self.mock_dynamodb.start()
        self.mock_sqs.start()

    def stop_mocking(self):
        """Method to stop mocking"""
        self.mock_s3.stop()
        self.mock_dynamodb.stop()
        self.mock_sqs.stop()

    # ***** Cuboid Index Table *****
    def _create_index_table(self, table_name, schema_file):
        """Method to create the S3 index table"""

        # Load json spec
        with open(schema_file) as handle:
            json_str = handle.read()
            table_params = json.loads(json_str)

        # Create table
        client = boto3.client('dynamodb', region_name=get_region())
        _ = client.create_table(TableName=table_name, **table_params)

        return client.get_waiter('table_exists')

    def create_index_table(self, table_name, schema_file):
        """Method to create DynamoDB index table"""
        if self.mock:
            mock_dynamodb2(self._create_index_table(table_name, schema_file))
        else:
            waiter = self._create_index_table(table_name, schema_file)

            # Wait for actual table to be ready.
            self.wait_table_create(table_name)

    def _delete_s3_index_table(self, table_name):
        """Method to delete the S3 index table"""
        client = boto3.client('dynamodb', region_name=get_region())
        client.delete_table(TableName=table_name)

    def delete_s3_index_table(self, table_name):
        """Method to create the S3 index table"""
        if self.mock:
            mock_dynamodb2(self._delete_s3_index_table(table_name))
        else:
            self._delete_s3_index_table(table_name)

            # Wait for table to be deleted (since this is real)
            self.wait_table_delete(table_name)

    def wait_table_create(self, table_name):
        """Poll dynamodb at a 2s interval until the table creates."""
        client = boto3.client('dynamodb', region_name=get_region())
        cnt = 0
        while True:
            time.sleep(2)
            cnt += 1
            if cnt > 50:
                # Give up waiting.
                return
            try:
                print('-', end='', flush=True)
                resp = client.describe_table(TableName=table_name)
                if resp['Table']['TableStatus'] == 'ACTIVE':
                    return
            except:
                # May get an exception if table doesn't currently exist.
                pass

    def wait_table_delete(self, table_name):
        """Poll dynamodb at a 2s interval until the table deletes."""
        client = boto3.client('dynamodb', region_name=get_region())
        cnt = 0
        while True:
            time.sleep(2)
            cnt += 1
            if cnt > 50:
                # Give up waiting.
                return
            try:
                print('-', end='', flush=True)
                resp = client.describe_table(TableName=table_name)
            except:
                # Exception thrown when table doesn't exist.
                print('')
                return

    # ***** END Cuboid Index Table END *****

    # ***** Cuboid Bucket *****
    def _create_cuboid_bucket(self, bucket_name):
        """Method to create the S3 bucket for cuboid storage"""
        client = boto3.client('s3', region_name=get_region())
        _ = client.create_bucket(
            ACL='private',
            Bucket=bucket_name
        )
        return client.get_waiter('bucket_exists')

    def create_cuboid_bucket(self, bucket_name):
        """Method to create the S3 bucket for cuboid storage"""
        if self.mock:
            mock_s3(self._create_cuboid_bucket(bucket_name))
        else:
            waiter = self._create_cuboid_bucket(bucket_name)

            # Wait for bucket to exist
            waiter.wait(Bucket=bucket_name)

    def _delete_cuboid_bucket(self, bucket_name):
        """Method to delete the S3 bucket for cuboid storage"""
        s3 = boto3.resource('s3', region_name=get_region())
        bucket = s3.Bucket(bucket_name)
        for obj in bucket.objects.all():
            obj.delete()

        # Delete bucket
        bucket.delete()
        return bucket

    def delete_cuboid_bucket(self, bucket_name):
        """Method to create the S3 bucket for cuboid storage"""
        if self.mock:
            mock_s3(self._delete_cuboid_bucket(bucket_name))
        else:
            bucket = self._delete_cuboid_bucket(bucket_name)
            # Wait for table to be deleted (since this is real)
            bucket.wait_until_not_exists()
    # ***** END Cuboid Bucket *****

    # ***** Flush SQS Queue *****
    def _create_flush_queue(self, queue_name):
        """Method to create a test sqs for flushing cubes"""
        client = boto3.client('sqs', region_name=get_region())
        response = client.create_queue(QueueName=queue_name)
        url = response['QueueUrl']
        return url

    def create_flush_queue(self, queue_name):
        """Method to create a test sqs for flushing cubes"""
        if self.mock:
            url = mock_sqs(self._create_flush_queue(queue_name))
        else:
            url = self._create_flush_queue(queue_name)
            time.sleep(10)
        return url

    def _delete_flush_queue(self, queue_url):
        """Method to delete a test sqs for flushing cubes"""
        client = boto3.client('sqs', region_name=get_region())
        client.delete_queue(QueueUrl=queue_url)

    def delete_flush_queue(self, queue_name):
        """Method to delete a test sqs for flushing cubes"""
        if self.mock:
            mock_sqs(self._delete_flush_queue(queue_name))
        else:
            self._delete_flush_queue(queue_name)
    # ***** END Flush SQS Queue *****

    def get_image8_dict(self):
        """Method to get the config dictionary for an image8 resource"""
        data = get_image_dict()
        return data

    def get_image16_dict(self):
        """Method to get the config dictionary for an image16 resource"""
        data = self.get_image8_dict()
        data['channel']['datatype'] = 'uint16'
        return data

    def get_anno64_dict(self):
        """Method to get the config dictionary for an image16 resource"""
        data = self.get_image8_dict()
        data['channel']['datatype'] = 'uint64'
        data['channel']['type'] = 'annotation'
        return data


class AWSSetupLayer(object):
    """A nose2 layer for setting up temporary AWS resources for testing ONCE per run"""
    setup_helper = SetupTests()
    data = None
    resource = None
    kvio_config = None
    state_config = None
    object_store_config = None

    @classmethod
    def setUp(cls):
        cls.setup_helper.mock = False

        # Setup Data
        cls.data = get_image_dict()
        cls.resource = BossResourceBasic(cls.data)

        config = configuration.BossConfig()

        # Get domain info
        parts = config['aws']['cache'].split('.')
        domain = "{}.{}".format(parts[1], parts[2])

        # kvio settings
        cls.kvio_config = {"cache_host": config['aws']['cache'],
                           "cache_db": 1,
                           "read_timeout": 86400}

        # state settings
        cls.state_config = {"cache_state_host": config['aws']['cache-state'], "cache_state_db": 1}

        _, domain = config['aws']['cuboid_bucket'].split('.', 1)
        cls.s3_flush_queue_name = "intTest.S3FlushQueue.{}".format(domain).replace('.', '-')
        cls.object_store_config = {"s3_flush_queue": "",
                                   "cuboid_bucket": "intTest{}.{}".format(random.randint(0,999), config['aws']['cuboid_bucket']),
                                   "page_in_lambda_function": config['lambda']['page_in_function'],
                                   "page_out_lambda_function": config['lambda']['flush_function'],
                                   "s3_index_table": "intTest.{}".format(config['aws']['s3-index-table']),
                                   "id_index_table": "intTest.{}".format(config['aws']['id-index-table']),
                                   "id_count_table": "intTest.{}".format(config['aws']['id-count-table'])}

        # Setup AWS
        print('Creating Temporary AWS Resources', end='', flush=True)
        try:
            cls.setup_helper.create_index_table(cls.object_store_config["s3_index_table"], cls.setup_helper.DYNAMODB_SCHEMA )
        except ClientError:
            cls.setup_helper.delete_s3_index_table(cls.object_store_config["s3_index_table"])
            cls.setup_helper.create_index_table(cls.object_store_config["s3_index_table"], cls.setup_helper.DYNAMODB_SCHEMA)

        try:
            cls.setup_helper.create_index_table(cls.object_store_config["id_index_table"], cls.setup_helper.ID_INDEX_SCHEMA )
        except ClientError:
            cls.setup_helper.delete_s3_index_table(cls.object_store_config["id_index_table"])
            cls.setup_helper.create_index_table(cls.object_store_config["id_index_table"], cls.setup_helper.ID_INDEX_SCHEMA )

        try:
            cls.setup_helper.create_index_table(cls.object_store_config["id_count_table"], cls.setup_helper.ID_COUNT_SCHEMA )
        except ClientError:
            cls.setup_helper.delete_s3_index_table(cls.object_store_config["id_count_table"])
            cls.setup_helper.create_index_table(cls.object_store_config["id_count_table"], cls.setup_helper.ID_COUNT_SCHEMA )

        try:
            cls.setup_helper.create_cuboid_bucket(cls.object_store_config["cuboid_bucket"])
        except ClientError:
            cls.setup_helper.delete_cuboid_bucket(cls.object_store_config["cuboid_bucket"])
            cls.setup_helper.create_cuboid_bucket(cls.object_store_config["cuboid_bucket"])

        try:
            cls.object_store_config["s3_flush_queue"] = cls.setup_helper.create_flush_queue(cls.s3_flush_queue_name)
        except ClientError:
            try:
                cls.setup_helper.delete_flush_queue(cls.object_store_config["s3_flush_queue"])
            except:
                pass
            time.sleep(61)
            cls.object_store_config["s3_flush_queue"] = cls.setup_helper.create_flush_queue(cls.s3_flush_queue_name)
        print('Done', flush=True)

    @classmethod
    def tearDown(cls):
        print('Deleting Temporary AWS Resources', end='', flush=True)
        try:
            cls.setup_helper.delete_s3_index_table(cls.object_store_config["s3_index_table"])
        except:
            pass

        try:
            cls.setup_helper.delete_cuboid_bucket(cls.object_store_config["cuboid_bucket"])
        except:
            pass

        try:
            cls.setup_helper.delete_flush_queue(cls.object_store_config["s3_flush_queue"])
        except:
            pass
        print('Done', flush=True)