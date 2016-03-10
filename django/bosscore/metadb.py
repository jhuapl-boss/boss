from bossutils.aws import *
import sys

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()

class MetaDB:
    def __init__(self, tablename):
        """
        Iniatialize the data base
        :param tablename:  Name of the meta data table
        """
        # Get a session from AWS manager
        aws_mngr = get_aws_manager()
        self.__session = aws_mngr.get_session()

        # Get table
        dynamodb = self.__session.resource('dynamodb')
        if 'test' in sys.argv:
            tablename = config["aws"]["test-meta-db"]
        else:
            tablename = config["aws"]["meta-db"]
        self.table = dynamodb.Table(tablename)

    def __del__(self):
        # Clean up session by returning it to the pool
        aws_mngr = get_aws_manager()
        aws_mngr.put_session(self.__session)

    def writemeta(self, metakey, value):
        """
        Store meta data in the Dynamo table
        :param metakey: Meta data key - Combination of the boss data model key and meta data key
        :param value: Meta data value
        """
        response = self.table.put_item(
            Item={
                'metakey': metakey,
                'metavalue': value,
            }
        )

    def getmeta(self, metakey):
        """
        Retrieve the meta data for a given key
        :param metakey:
        :return:
        """
        response = self.table.get_item(
            Key={
                'metakey': metakey,
            }
        )
        if 'Item' in response:
            return response['Item']
        else:
            return None

    def deletemeta(self, metakey):
        """
        Delete the meta data item for the specified key
        :param metakey: Meta data key to be delete
        :return:
        """
        response = self.table.delete_item(
            Key={
                'metakey': metakey,
            },
            ReturnValues='ALL_OLD'
        )
        return response

    def updatemeta(self, metakey, newvalue):
        """
        Update the Value for the given key
        :param metakey: Search key
        :param newvalue: New value for the meta data key
        :return:
        """
        response = self.table.update_item(
            Key={
                'metakey': metakey,
            },
            UpdateExpression='SET metavalue = :val1',
            ExpressionAttributeValues={
                ':val1': newvalue
            },
            ReturnValues='UPDATED_NEW'
        )
        return response
