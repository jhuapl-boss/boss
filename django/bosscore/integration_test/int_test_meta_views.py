
from rest_framework.test import APITestCase
from ..models import *
from ..test.test_meta_views import MetaServiceViewTestsMixin
from .setup_db import setupTestDB
import bossutils
import boto3
from bossutils.aws import *
import json


from django.conf import settings
version  = settings.BOSS_VERSION

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()
testtablename = config["aws"]["test-meta-db"]
aws_mngr = get_aws_manager()


class BossCoreMetaServiceViewIntegrationTests(MetaServiceViewTestsMixin, APITestCase):
    """
    Class to tests the bosscore views for the metadata service

    Uses Vault and AWS's DynamoDB (as opposed to a local DynamoDB).
    """
    @classmethod
    def setUpClass(cls):
        cls.__session = aws_mngr.get_session()

        # Load table info
        cfgfile = open('bosscore/dynamo_schema.json', 'r')
        tblcfg = json.load(cfgfile)

        # Get table
        dynamodb = cls.__session.resource('dynamodb')
        cls.table = dynamodb.create_table(TableName=testtablename, **tblcfg)
        cls.table.meta.client.get_waiter('table_exists').wait(TableName=testtablename)

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        cls.table.meta.client.get_waiter('table_not_exists').wait(TableName=testtablename)
