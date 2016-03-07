
from rest_framework.test import APITestCase
from ..models import *

from django.conf import settings
version  = settings.BOSS_VERSION


class BossCoreMetaServiceViewTests(APITestCase):
    """
    Class to tests the bosscore views for the metadata service
    """

    def setUp(self):
        """
        Initialize the  database with a some objects to test
        :return:
        """
        col = Collection.objects.create(name='col1')
        cf = CoordinateFrame.objects.create(name='cf1', description ='cf1',
                                            x_start=0, x_stop=1000,
                                            y_start=0, y_stop=1000,
                                            z_start=0, z_stop=1000,
                                            x_voxel_size=4, y_voxel_size=4, z_voxel_size=4,
                                            time_step=1
                                            )
        exp = Experiment.objects.create(name='exp1', collection=col, coord_frame=cf)

        channel = ChannelLayer.objects.create(name='channel1', experiment=exp, is_channel=True, default_time_step = 1)
        layer = ChannelLayer.objects.create(name='layer1', experiment=exp, is_channel=False, default_time_step = 1)

    def test_meta_data_service_collection(self):
        """
        Test to make sure the meta URL for get, post, delete and update with all\
        datamodel params resolves to the meta view
        :return:
        """
        baseurl = '/' + version + '/meta/col1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metadata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_experiment(self):
        """
        Test to make sure the meta URL for get, post, delete and update with an experiment
        :return:
        """
        baseurl = '/' + version + '/meta/col1/exp1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_channel(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/channel1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_layer(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/layer1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection

        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)
