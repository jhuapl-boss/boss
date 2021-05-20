#!/usr/bin/env python3

"""
Create the metadata table in a local DynamoDB for easy testing.

Start a local Keycloak instance (see boss-manage/local_testing-support/keycloak-docker/keycloak-11.0.0).

Start Django with (note using a different port for Django since local Dynamo
defaults to 8000):

DYNAMO_URL=http://localhost:8000 python manage.py runserver --settings=boss.settings.keycloak 127.0.0.1:8086
"""

import boto3
from configparser import ConfigParser
import json

def run():
    boss_config = ConfigParser()
    boss_config.read('/etc/boss/boss.config')
    table_name = boss_config['aws']['meta-db']

    with open('bosscore/dynamo_schema.json') as fp:
        args = json.load(fp)
    args['TableName'] = table_name

    client = boto3.client('dynamodb', endpoint_url='http://localhost:8000')
    client.create_table(**args)


if __name__ == '__main__':
    run()

