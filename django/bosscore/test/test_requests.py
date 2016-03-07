from rest_framework.test import APITestCase
from django.http import HttpRequest
from rest_framework.request import Request

from ..request import BossRequest
from ..models import *
from django.conf import settings
version  = settings.BOSS_VERSION


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
        cf = CoordinateFrame.objects.create(name='cf1', description ='cf1',
                                            x_start=0, x_stop=1000,
                                            y_start=0, y_stop=1000,
                                            z_start=0, z_stop=1000,
                                            x_voxel_size=4, y_voxel_size=4, z_voxel_size=4,
                                            time_step=1
                                            )
        exp = Experiment.objects.create(name='exp1', collection=col, coord_frame=cf, num_hierarchy_levels=10)
        channel = ChannelLayer.objects.create(name='channel1', experiment=exp, is_channel=True, default_time_step = 1)
        layer = ChannelLayer.objects.create(name='layer1', experiment=exp, is_channel=False, default_time_step = 1)

        channel = ChannelLayer.objects.create(name='channel2', experiment=exp, is_channel=True, default_time_step = 1)
        layer = ChannelLayer.objects.create(name='layer2', experiment=exp, is_channel=False, default_time_step = 1)

    def test_request_cutout_init_channel(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel1'
        bosskey = 'col1&exp1&channel1'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_channel_layer(), channel)
        self.assertEqual(ret.get_bosskey(), bosskey)

    def test_request_cutout_init_layer(self):
        """
        Test initialization of cutout requests for the datamodel
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/layer1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        layer = 'layer1'
        bosskey = 'col1&exp1&layer1'

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version

        ret = BossRequest(drfrequest)
        self.assertEqual(ret.get_collection(), col)
        self.assertEqual(ret.get_experiment(), exp)
        self.assertEqual(ret.get_channel_layer(), layer)
        self.assertEqual(ret.get_bosskey(), bosskey)

    def test_request_cutout_init_cutoutargs_channel(self):
        """
        Test initialization of cutout arguments for a cutout request
        :return:
        """
        url = '/' + version + '/cutout/col1/exp1/channel1/2/0:5/0:6/0:2/'
        col = 'col1'
        exp = 'exp1'
        channel = 'channel1'
        bosskey = 'col1&exp1&channel1'

        res = 2
        (x_start, x_stop) = (0, 5)
        (y_start, y_stop) = (0, 6)
        (z_start, z_stop) = (0, 2)

        # Create the request
        req = HttpRequest()
        req.META = {'PATH_INFO': url}
        drfrequest = Request(req)
        drfrequest.version = version 
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
