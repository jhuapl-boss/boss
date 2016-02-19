from rest_framework.test import APITestCase
from django.http import HttpRequest
from rest_framework.request import Request

from .request import BossRequest
from .models import Collection, Experiment, Dataset, Channel, CoordinateFrame, TimeSample, Layer


class BossCoreRequestTests(APITestCase):
    """
    Class to test boss requests
    """

    def setUp(self):
        """
        Initialize the database
        :return:
        """
        col = Collection.objects.create(name='col1')
        exp = Experiment.objects.create(name='exp1', collection=col, num_resolution_levels=5)
        cf = CoordinateFrame.objects.create(name='cf1', x_extent=1000, y_extent=10000, z_extent=10000,
                                                    x_voxelsize=4, y_voxelsize=4, z_voxelsize=4)
        ds = Dataset.objects.create(name='ds1', experiment=exp, coord_frame=cf)
        channel = Channel.objects.create(name='channel1', dataset=ds)
        ts = TimeSample.objects.create(name='ts1', channel=channel)
        layer = Layer.objects.create(name='layer1', time=ts)
        extralayer = Layer.objects.create(name='layerx', time=ts)

        ds.default_channel = channel
        ds.default_time = ts
        ds.default_layer = layer
        ds.save()

        ds = Dataset.objects.create(name='ds5', experiment=exp, coord_frame=cf)
        channel = Channel.objects.create(name='channel5', dataset=ds)
        ts = TimeSample.objects.create(name='ts5', channel=channel)
        layer = Layer.objects.create(name='layer5', time=ts)

    def test_request_cutout_init(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/v0.2/cutout/col1/exp1/ds1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        ds = 'ds1'
        channel = 'channel1'
        ts = 'ts1'
        layer = 'layer1'
        bosskey = 'col1&exp1&ds1&channel1&ts1&layer1'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.query_params['channel'] = 'channel1'
        drfrequest.query_params['timesample'] = 'ts1'
        drfrequest.query_params['layer'] = 'layer1'

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_dataset(), ds)
        self.assertEqual(ret.get_channel(), channel)
        self.assertEqual(ret.get_timesample(), ts)
        self.assertEqual(ret.get_layer(), layer)
        self.assertEqual(ret.get_bosskey(), bosskey)

        # Create the request with no optional arguments to test assignment of defaults
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_dataset(), ds)
        self.assertEqual(ret.get_channel(), channel)
        self.assertEqual(ret.get_timesample(), ts)
        self.assertEqual(ret.get_layer(), layer)
        self.assertEqual(ret.get_bosskey(), bosskey)

        # Test optional arguments with layer
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        #        drfrequest.query_params['channel'] = 'channel1'
        #        drfrequest.query_params['timesample'] = 'ts1'
        drfrequest.query_params['layer'] = 'layerx'

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_dataset(), ds)
        self.assertEqual(ret.get_channel(), channel)
        self.assertEqual(ret.get_timesample(), ts)
        self.assertEqual(ret.get_layer(), 'layerx')
        self.assertEqual(ret.get_bosskey(), 'col1&exp1&ds1&channel1&ts1&layerx')

    def test_request_cutout_init_cutoutargs(self):
        """
        Test initialization of cutout arguments for a cutout request
        :return:
        """
        url = '/v0.2/cutout/col1/exp1/ds1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        ds = 'ds1'
        channel = 'channel1'
        ts = 'ts1'
        layer = 'layer1'
        bosskey = 'col1&exp1&ds1&channel1&ts1&layer1'

        res = 2
        (x_start, x_stop) = (0, 5)
        (y_start, y_stop) = (0, 6)
        (z_start, z_stop) = (0, 2)

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        ret = BossRequest(drfrequest)

        self.assertEqual(ret.get_resolution(), res)
        self.assertEqual(ret.get_x_start(), x_start)
        self.assertEqual(ret.get_x_stop(), x_stop)
        self.assertEqual(ret.get_x_span(), x_stop - x_start)

        self.assertEqual(ret.get_y_start(), y_start)
        self.assertEqual(ret.get_y_stop(), y_stop)
        self.assertEqual(ret.get_y_span(), y_stop - y_start)

        self.assertEqual(ret.get_z_start(), z_start)
        self.assertEqual(ret.get_z_stop(), z_stop)
        self.assertEqual(ret.get_z_span(), z_stop - z_start)
