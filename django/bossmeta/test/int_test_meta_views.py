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

import bossutils
from bossutils.aws import *
from django.conf import settings
from rest_framework.test import APITestCase

from bossmeta.test.test_meta_views import MetaServiceViewTestsMixin
from botocore.exceptions import ClientError

version = settings.BOSS_VERSION

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()
testtablename = "test." + config["aws"]["meta-db"]


class BossCoreMetaServiceViewIntegrationTests(MetaServiceViewTestsMixin, APITestCase):
    """
    Class to tests the bosscore views for the metadata service

    Uses Vault and AWS's DynamoDB (as opposed to a local DynamoDB).
    """
    @classmethod
    def setUpTestData(cls):
        # Load table info
        cfgfile = open('bosscore/dynamo_schema.json', 'r')
        tblcfg = json.load(cfgfile)

        # Get table
        client = boto3.client('dynamodb', region_name=get_region())
        try:
            client.create_table(TableName=testtablename, **tblcfg)
        except ClientError:
            client.delete_table(TableName=testtablename)
            waiter = client.get_waiter('table_not_exists')
            waiter.wait(TableName=testtablename)
            client.create_table(TableName=testtablename, **tblcfg)

        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=testtablename)

    @classmethod
    def tearDownClass(cls):
        super(BossCoreMetaServiceViewIntegrationTests, cls).tearDownClass()
        client = boto3.client('dynamodb', region_name=get_region())
        client.delete_table(TableName=testtablename)
        waiter = client.get_waiter('table_not_exists')
        waiter.wait(TableName=testtablename)
