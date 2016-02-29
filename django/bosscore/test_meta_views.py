
from rest_framework.test import APITestCase
from .models import *

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
        exp = Experiment.objects.create(name='exp1', collection=col)
        cf = CoordinateFrame.objects.create(name='cf1', x_extent=1000, y_extent=10000, z_extent=10000,
                                                    x_voxelsize=4, y_voxelsize=4, z_voxelsize=4)
        ds = Dataset.objects.create(name='dataset1', experiment=exp, coord_frame=cf)

        channel = Channel.objects.create(name='channel1', dataset=ds)
        ts = TimeSample.objects.create(name='ts1', channel=channel)
        layer = Layer.objects.create(name='layer1', time=ts)
        ds.default_channel = channel
        ds.default_time = ts
        ds.default_layer = layer
        ds.save()

        ds = Dataset.objects.create(name='ds5', experiment=exp, coord_frame=cf)
        channel = Channel.objects.create(name='channel5', dataset=ds)
        ts = TimeSample.objects.create(name='ts5', channel=channel)
        layer = Layer.objects.create(name='layer5', time=ts)

    def test_meta_data_service_collection(self):
        """
        Test to make sure the meta URL for get, post, delete and update with all\
        datamodel params resolves to the meta view
        :return:
        """
        baseurl = '/' + version + '/meta/col1/'
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
        self.assertEqual(response.data['metakey'], 'col1#testmkey')
        self.assertEqual(response.data['metavalue'], 'TestStringModified')

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
        self.assertEqual(response.data['metakey'], 'col1&exp1#testmkey')
        self.assertEqual(response.data['metavalue'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_dataset(self):
        """
        Test to make sure the meta URL for get, post, delete and update with an dataset
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/dataset1/'
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
        self.assertEqual(response.data['metakey'], 'col1&exp1&dataset1#testmkey')
        self.assertEqual(response.data['metavalue'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_channel(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/dataset1/'
        argspost = '?channel=channel1&key=testmkey&value=TestString'
        argsget = '?channel=channel1&key=testmkey'

        # Post a new metedata object for the collection

        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?channel=channel1&key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['metakey'], 'col1&exp1&dataset1&channel1#testmkey')
        self.assertEqual(response.data['metavalue'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_timesample(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a timesample
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/dataset1/'
        argspost = '?channel=channel1&time=ts1&key=testmkey&value=TestString'
        argsget = '?channel=channel1&time=ts1&key=testmkey'

        # Post a new metedata object for the collection

        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?channel=channel1&time=ts1&key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['metakey'], 'col1&exp1&dataset1&channel1&ts1#testmkey')
        self.assertEqual(response.data['metavalue'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_layer(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a layer
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/dataset1/'
        argspost = '?channel=channel1&time=ts1&layer=layer1&key=testmkey&value=TestString'
        argsget = '?channel=channel1&time=ts1&layer=layer1&key=testmkey'

        # Post a new metedata object for the collection

        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?channel=channel1&time=ts1&layer=layer1&key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['metakey'], 'col1&exp1&dataset1&channel1&ts1&layer1#testmkey')
        self.assertEqual(response.data['metavalue'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)
