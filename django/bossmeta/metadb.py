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
import os
import sys

from bossutils.aws import *
from boto3.dynamodb.conditions import Key

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()
tablename = config["aws"]["meta-db"]

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()


class MetaDB:
    def __init__(self):
        """
        Initialize the data base
        Returns:

        """
        self.__local_dynamo = os.environ.get('USING_DJANGO_TESTRUNNER') is not None
        if not self.__local_dynamo:
            session = get_session()
            dynamodb = session.resource('dynamodb')
            if 'test' in sys.argv:
                # TODO: This needs to be made more robust. Parameters should be mocked, not assumed.
                tablename = 'intTest.' + config["aws"]["meta-db"]
            else:
                tablename = config["aws"]["meta-db"]
        else:
            tablename = config["aws"]["meta-db"]
            session = boto3.Session(aws_access_key_id='foo', aws_secret_access_key='foo')
            dynamodb = session.resource('dynamodb', region_name='us-east-1', endpoint_url='http://localhost:8000')

        self.table = dynamodb.Table(tablename)

    def write_meta(self, lookup_key, key, value):
        """
        Write the  meta data to dyanmodb
        Args:
            lookup_key: Key for the object requested
            key: Meta data key
            value: Metadata value

        Returns:

        """

        response = self.table.put_item(
            Item={
                'lookup_key': lookup_key,
                'key': key,
                'metavalue': value,
            }
        )
        return response

    def get_meta(self, lookup_key, key):
        """
        Retrieve the meta data for a given key
        Args:
            lookup_key: Key for the object requested
            key: Metadata key

        Returns:

        """

        response = self.table.get_item(
            Key={
                'lookup_key': lookup_key,
                'key': key,
            }
        )
        if 'Item' in response:
            return response['Item']
        else:
            return None

    def delete_meta(self, lookup_key, key):
        """
        Delete the meta data item for the specified key
        Args:
            lookup_key: Key for the object requested
            key: Metadata key

        Returns:

        """

        response = self.table.delete_item(
            Key={
                'lookup_key': lookup_key,
                'key': key,
            },
            ReturnValues='ALL_OLD'
        )
        return response

    def update_meta(self, lookup_key, key, new_value):
        """
        Update the Value for the given key
        Args:
            lookup_key: Key for the object requested
            key: Metadata key
            new_value: New meta data value

        Returns:

        """

        response = self.table.update_item(
            Key={
                'lookup_key': lookup_key,
                'key': key,
            },
            UpdateExpression='SET metavalue = :val1',
            ExpressionAttributeValues={
                ':val1': new_value
            },
            ReturnValues='UPDATED_NEW'
        )
        return response

    def get_meta_list(self, lookup_key):
        """
        Retrieve all the meta data for a given object using the lookupley
        Args:
            lookup_key: Key for the object requested
        Returns:

        """
        response = self.table.query(
            KeyConditionExpression=Key('lookup_key').eq(lookup_key)
        )

        if 'Items' in response:
            return response['Items']
        else:
            return None
