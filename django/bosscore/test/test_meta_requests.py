from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory

from ..request import BossRequest
from ..views import BossMeta
from ..models import *
from .setup_db import setupTestDB
from django.contrib.auth.models import User
from rest_framework.test import APIClient


from django.conf import settings
version  = settings.BOSS_VERSION

class BossCoreMetaRequestTests(APITestCase):
    """
    Class to test Meta data requests
    """

    def setUp(self):
        """
        Initialize the test database with some objects
        :return:
        """
        self.rf = APIRequestFactory()
        setupTestDB.insert_test_data()
        self.user = User.objects.get(username='testuser')



    def test_bossrequest_init_collection(self):
        """
        Test initialization of requests from the meta data service with collection
        :return:
        """
        # create the request with collection name
        url = '/' + version + '/meta/col1/?key=mkey'
        expectedValue = 'col1'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), expectedValue)

    def test_bossrequest_init_experiment(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment
        :return:
        """
        # create the request with collection name and experiment name
        url = '/' + version + '/meta/col1/exp1/?key=mkey'
        expectedCol = 'col1'
        expectedExp = 'exp1'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), expectedCol)
        self.assertEqual(ret.get_experiment(), expectedExp)

    def test_bossrequest_init_channel(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment and channel
        :return:
        """
        # create the request with collection name and experiment name and channel name
        url = '/' + version + '/meta/col1/exp1/channel1/'
        expectedCol = 'col1'
        expectedExp = 'exp1'
        expectedChannel = 'channel1'

        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), expectedCol)
        self.assertEqual(ret.get_experiment(), expectedExp)
        self.assertEqual(ret.get_channel_layer(), expectedChannel)


    def test_bossrequest_init_layer(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment and channel
        :return:
        """
        # create the request with collection name and experiment name and channel name
        url = '/' + version + '/meta/col1/exp1/layer1/'
        expectedCol = 'col1'
        expectedExp = 'exp1'
        expectedLayer = 'layer1'

        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), expectedCol)
        self.assertEqual(ret.get_experiment(), expectedExp)
        self.assertEqual(ret.get_channel_layer(), expectedLayer)

    def test_bossrequest_init_coordinateframe(self):
        """
        Test initialization of requests from the meta data service with a valid collection and experiment and dataset
        :return:
        """
        # create the request with collection name and experiment name and dataset name
        url = '/' + version + '/meta/col1/exp1/channel1/?key=mkey'
        expectedCol = 'col1'
        expectedExp = 'exp1'
        expectedChannel = 'channel1'
        expectedCoord = 'cf1'

        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), expectedCol)
        self.assertEqual(ret.get_experiment(), expectedExp)
        self.assertEqual(ret.get_channel_layer(), expectedChannel)

        # Check coordinate frame
        self.assertEqual(ret.get_coordinate_frame(), expectedCoord)



    def test_get_bosskey_collection(self):
        """
        Test retriving a bossmeta key from  BossRequest object with collection name
        """
        # create the request
        url = '/' +version + '/meta/col1/?key=mkey'
        expectedValue = 'col1'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        drfrequest.user = self.user

        ret = BossRequest(drfrequest)
        boss_key = ret.get_boss_key()
        self.assertEqual(ret.get_collection(), expectedValue)
        self.assertEqual(boss_key[0], expectedValue)

    def test_get_boss_key_experiment(self):
        """
        Test retriving a bossmeta key from  BossRequest object with collection name and experimentname
        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/?key=mkey'
        expectedValue = 'col1&exp1'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        drfrequest.user = self.user

        ret = BossRequest(drfrequest)
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key[0], expectedValue)

    def test_get_boss_key_channel(self):
        """
        Test retriving a bossmeta key from  BossRequest object with collection name and experimentname
        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/channel1/?key=mkey'
        expectedValue = 'col1&exp1&channel1'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        drfrequest.user = self.user

        ret = BossRequest(drfrequest)
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key[0], expectedValue)

    def test_get_boss_key_layer(self):
        """
        Test retriving a bossmeta key from  BossRequest object with collection name and experimentname
        """
        # create the request
        url = '/' + version + '/meta/col1/exp1/layer1/?key=mkey'
        expectedValue = 'col1&exp1&layer1'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        drfrequest.user = self.user

        ret = BossRequest(drfrequest)
        boss_key = ret.get_boss_key()
        self.assertEqual(boss_key[0], expectedValue)

    def test_get_key(self):
        """
        Test the the get meta key method
        """
        url = '/' + version + '/meta/col1/exp1/channel1/?key=mkey'
        expectedValue = 'mkey'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        drfrequest.user = self.user

        ret = BossRequest(drfrequest)
        key = ret.get_key()
        self.assertEqual(key, expectedValue)

    def test_get_value(self):
        """
        Test the the get meta key method
        """
        url = '/' + version + '/meta/col1/exp1/layer1/?key=mkey&value=TestValue'
        expectedValue = 'TestValue'
        request = self.rf.get(url)
        drfrequest = BossMeta().initialize_request(request)
        drfrequest.version = version
        drfrequest.user = self.user

        ret = BossRequest(drfrequest)
        value = ret.get_value()
        self.assertEqual(value, expectedValue)
