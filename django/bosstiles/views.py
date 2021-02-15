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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

from boss import utils
from boss.throttling import BossThrottle
from bosscore.models import ThrottleMetric
from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, ErrorCodes
from bossutils.logger import bossLogger

import spdb

import bossutils

from .renderers import PNGRenderer, JPEGRenderer


class CutoutTile(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    renderer_classes = (PNGRenderer, JPEGRenderer)

    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    def get(self, request, collection, experiment, channel, orientation, resolution, x_args, y_args, z_args, t_args=None):
        """
        View to handle GET requests for a cuboid of data while providing all params

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param channel: Channel identifier, indicating which channel you want to access
        :param orientation: Image plane requested. Vaid options include xy,xz or yz
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_args: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_args: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_args: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """
        # Process request and validate
        try:
            request_args = {
                "service": "image",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "orientation" : orientation,
                "resolution": resolution,
                "x_args": x_args,
                "y_args": y_args,
                "z_args": z_args,
                "time_args": t_args
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        #Define access mode
        access_mode = utils.get_access_mode(request)

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            self.bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossHTTPError("Datatype does not match channel", ErrorCodes.DATATYPE_DOES_NOT_MATCH)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * (self.bit_depth/8)
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossHTTPError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                 ErrorCodes.REQUEST_TOO_LARGE)

        # Add metrics to CloudWatch
        cost = ( req.get_x_span()
               * req.get_y_span()
               * req.get_z_span()
               * (req.get_time().stop - req.get_time().start)
               * self.bit_depth
               / 8
               ) # Calculating the number of bytes

        BossThrottle().check('image',ThrottleMetric.METRIC_TYPE_EGRESS,
                             request.user,
                             cost,ThrottleMetric.METRIC_UNITS_BYTES)

        boss_config = bossutils.configuration.BossConfig()
        dimensions = [
            {'Name': 'User', 'Value': request.user.username},
            {'Name': 'Resource', 'Value': '{}/{}/{}'.format(collection,
                                                            experiment,
                                                            channel)},
            {'Name': 'Stack', 'Value': boss_config['system']['fqdn']},
        ]

        session = bossutils.aws.get_session()
        client = session.client('cloudwatch')

        try:
            client.put_metric_data(
                Namespace="BOSS/Image",
                MetricData=[{
                    'MetricName': 'InvokeCount',
                    'Dimensions': dimensions,
                    'Value': 1.0,
                    'Unit': 'Count'
                }, {
                    'MetricName': 'EgressCost',
                    'Dimensions': dimensions,
                    'Value': cost,
                    'Unit': 'Bytes'
                }]
            )
        except Exception as e:
            log = bossLogger()
            log.exception('Error during put_metric_data: {}'.format(e))
            log.exception('Allowing bossDB to continue after logging')



        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB(settings.KVIO_SETTINGS,
                                         settings.STATEIO_CONFIG,
                                         settings.OBJECTIO_CONFIG)

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Do a cutout as specified
        data = cache.cutout(resource, corner, extent, req.get_resolution(),
                            [req.get_time().start, req.get_time().stop], access_mode=access_mode)

        # Covert the cutout back to an image and return it
        if orientation == 'xy':
            img = data.xy_image()
        elif orientation == 'yz':
            img = data.yz_image()
        elif orientation == 'xz':
            img = data.xz_image()
        else:
            return BossHTTPError("Invalid orientation: {}".format(orientation),
                                 ErrorCodes.INVALID_CUTOUT_ARGS)

        return Response(img)


class Tile(APIView):
    """
    View to handle tile interface when accessing via tile indicies

    * Requires authentication.
    """
    renderer_classes = (PNGRenderer, JPEGRenderer)

    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    def get(self, request, collection, experiment, channel, orientation, tile_size, resolution, x_idx, y_idx, z_idx, t_idx=None):
        """
        View to handle GET requests for a tile when providing indices. Currently only supports XY plane

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param channel: Channel identifier, indicating which channel you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_idx: the tile index in the X dimension
        :param y_idx: the tile index in the Y dimension
        :param z_idx: the tile index in the Z dimension
        :param t_idx: the tile index in the T dimension
        :return:
        """
        # TODO: DMK Merge Tile and Image view once updated request validation is sorted out
        # Process request and validate
        try:
            request_args = {
                "service": "tile",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "orientation": orientation,
                "tile_size": tile_size,
                "resolution": resolution,
                "x_args": x_idx,
                "y_args": y_idx,
                "z_args": z_idx,
                "time_args": t_idx
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        #Define access_mode
        access_mode = utils.get_access_mode(request)

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            self.bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossHTTPError("Datatype does not match channel", ErrorCodes.DATATYPE_DOES_NOT_MATCH)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * (self.bit_depth/8)
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossHTTPError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                 ErrorCodes.REQUEST_TOO_LARGE)

        # Add metrics to CloudWatch
        cost = ( req.get_x_span()
               * req.get_y_span()
               * req.get_z_span()
               * (req.get_time().stop - req.get_time().start)
               * self.bit_depth
               / 8
               ) # Calculating the number of bytes

        BossThrottle().check('tile',ThrottleMetric.METRIC_TYPE_EGRESS,
                             request.user,
                             cost,ThrottleMetric.METRIC_UNITS_BYTES)

        boss_config = bossutils.configuration.BossConfig()
        dimensions = [
            {'Name': 'User', 'Value': request.user.username},
            {'Name': 'Resource', 'Value': '{}/{}/{}'.format(collection,
                                                            experiment,
                                                            channel)},
            {'Name': 'Stack', 'Value': boss_config['system']['fqdn']},
        ]

        session = bossutils.aws.get_session()
        client = session.client('cloudwatch')

        try:
            client.put_metric_data(
                Namespace="BOSS/Tile",
                MetricData=[{
                    'MetricName': 'InvokeCount',
                    'Dimensions': dimensions,
                    'Value': 1.0,
                    'Unit': 'Count'
                }, {
                    'MetricName': 'EgressCost',
                    'Dimensions': dimensions,
                    'Value': cost,
                    'Unit': 'Bytes'
                }]
            )
        except Exception as e:
            log = bossLogger()
            log.exception('Error during put_metric_data: {}'.format(e))
            log.exception('Allowing bossDB to continue after logging')



        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB(settings.KVIO_SETTINGS,
                                         settings.STATEIO_CONFIG,
                                         settings.OBJECTIO_CONFIG)

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Do a cutout as specified
        data = cache.cutout(resource, corner, extent, req.get_resolution(),
                            [req.get_time().start, req.get_time().stop], access_mode=access_mode)

        # Covert the cutout back to an image and return it
        if orientation == 'xy':
            img = data.xy_image()
        elif orientation == 'yz':
            img = data.yz_image()
        elif orientation == 'xz':
            img = data.xz_image()
        else:
            return BossHTTPError("Invalid orientation: {}".format(orientation),
                                 ErrorCodes.INVALID_CUTOUT_ARGS)

        return Response(img)
