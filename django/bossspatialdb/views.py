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
import numpy as np
import boto3
import botocore.exceptions

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.parsers import JSONParser

from .parsers import BloscParser, BloscPythonParser, NpygzParser, is_too_large
from .renderers import BloscRenderer, BloscPythonRenderer, NpygzRenderer, JpegRenderer

from django.http import HttpResponse
from django.conf import settings

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, BossParserError, ErrorCodes
from bosscore.models import Channel

from boss import utils
from boss.throttling import BossThrottle
from bosscore.models import ThrottleMetric

from spdb.spatialdb.spatialdb import SpatialDB, CUBOIDSIZE
from spdb.spatialdb.rediskvio import RedisKVIO
from spdb import project
import bossutils
from bossutils.logger import bossLogger
from bossspatialdb.downsample import delete_queued_job, start


class Cutout(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    # Set Parser and Renderer
    parser_classes = (BloscParser, BloscPythonParser, NpygzParser, BrowsableAPIRenderer)
    renderer_classes = (BloscRenderer, BloscPythonRenderer, NpygzRenderer, JpegRenderer,
                        JSONRenderer, BrowsableAPIRenderer)

    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    def get(self, request, collection, experiment, channel, resolution, x_range, y_range, z_range, t_range=None):
        """
        View to handle GET requests for a cuboid of data while providing all params

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param channel: Channel identifier, indicating which channel you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """
        # Check if parsing completed without error. If an error did occur, return to user.
        if "filter" in request.query_params:
            ids = request.query_params["filter"]
        else:
            ids = None

        if "iso" in request.query_params:
            if request.query_params["iso"].lower() == "true":
                iso = True
            else:
                iso = False
        else:
            iso = False

        # Define access mode.
        access_mode = utils.get_access_mode(request)

        if isinstance(request.data, BossParserError):
            return request.data.to_http()

        # Process request and validate
        try:
            request_args = {
                "service": "cutout",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "resolution": resolution,
                "x_args": x_range,
                "y_args": y_range,
                "z_args": z_range,
                "time_args": t_range,
                "ids": ids
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # Convert to Resource
        resource = project.BossResourceDjango(req)

        # Get bit depth
        try:
            self.bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossHTTPError("Unsupported data type: {}".format(resource.get_data_type()), ErrorCodes.TYPE_ERROR)

        # Make sure cutout request is under 500MB UNCOMPRESSED
        if is_too_large(req, self.bit_depth):
            return BossHTTPError("Cutout request is over 500MB when uncompressed. Reduce cutout dimensions.",
                                 ErrorCodes.REQUEST_TOO_LARGE)

        # Add metrics to CloudWatch
        cost = ( req.get_x_span()
               * req.get_y_span()
               * req.get_z_span()
               * (req.get_time().stop - req.get_time().start)
               * self.bit_depth
               / 8
               ) # Calculating the number of bytes

        # seprate direction of movement from api and provide units of metric
        BossThrottle().check('cutout',ThrottleMetric.METRIC_TYPE_EGRESS,
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
                Namespace="BOSS/Cutout",
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
        cache = SpatialDB(settings.KVIO_SETTINGS,
                          settings.STATEIO_CONFIG,
                          settings.OBJECTIO_CONFIG)

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Get a Cube instance with all time samples
        data = cache.cutout(resource, corner, extent, req.get_resolution(), [req.get_time().start, req.get_time().stop],
                            filter_ids=req.get_filter_ids(), iso=iso, access_mode=access_mode)
        to_renderer = {"time_request": req.time_request,
                       "data": data}

        # Send data to renderer
        return Response(to_renderer)

    def post(self, request, collection, experiment, channel, resolution, x_range, y_range, z_range, t_range=None):
        """
        View to handle POST requests for a cuboid of data while providing all datamodel params

        Due to parser implementation, request.data should be a numpy array already.

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param channel: Channel identifier, indicating which dataset or annotation project you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """
        # Check if parsing completed without error. If an error did occur, return to user.
        if isinstance(request.data, BossParserError):
            return request.data.to_http()

        # Check for optional iso flag
        if "iso" in request.query_params:
            if request.query_params["iso"].lower() == "true":
                iso = True
            else:
                iso = False
        else:
            iso = False

        # Get BossRequest and BossResource from parser
        req = request.data[0]
        resource = request.data[1]

        # Get bit depth
        try:
            expected_data_type = resource.get_numpy_data_type()
        except ValueError:
            return BossHTTPError("Unsupported data type: {}".format(resource.get_data_type()), ErrorCodes.TYPE_ERROR)

        # Make sure datatype is valid
        if expected_data_type != request.data[2].dtype:
            return BossHTTPError("Datatype does not match channel", ErrorCodes.DATATYPE_DOES_NOT_MATCH)

        # Make sure the dimensions of the data match the dimensions of the post URL
        if len(request.data[2].shape) == 4:
            expected_shape = (len(req.get_time()), req.get_z_span(), req.get_y_span(), req.get_x_span())
        else:
            expected_shape = (req.get_z_span(), req.get_y_span(), req.get_x_span())

        if expected_shape != request.data[2].shape:
            return BossHTTPError("Data dimensions in URL do not match POSTed data.",
                                 ErrorCodes.DATA_DIMENSION_MISMATCH)

        # Add metrics to CloudWatch
        cost = ( req.get_x_span()
               * req.get_y_span()
               * req.get_z_span()
               * (req.get_time().stop - req.get_time().start)
               * resource.get_bit_depth()
               / 8
               ) # Calculating the number of bytes

        BossThrottle().check('cutout',ThrottleMetric.METRIC_TYPE_INGRESS,
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
                Namespace="BOSS/Cutout",
                MetricData=[{
                    'MetricName': 'InvokeCount',
                    'Dimensions': dimensions,
                    'Value': 1.0,
                    'Unit': 'Count'
                }, {
                    'MetricName': 'IngressCost',
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
        cache = SpatialDB(settings.KVIO_SETTINGS,
                          settings.STATEIO_CONFIG,
                          settings.OBJECTIO_CONFIG)

        # Write block to cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())

        try:
            if len(request.data[2].shape) == 4:
                cache.write_cuboid(resource, corner, req.get_resolution(), request.data[2], req.get_time()[0], iso=iso)
            else:
                cache.write_cuboid(resource, corner, req.get_resolution(),
                                   np.expand_dims(request.data[2], axis=0), req.get_time()[0], iso=iso)
        except Exception as e:
            # TODO: Eventually remove as this level of detail should not be sent to the user
            return BossHTTPError('Error during write_cuboid: {}'.format(e), ErrorCodes.BOSS_SYSTEM_ERROR)

        # If the channel status is DOWNSAMPLED change status to NOT_DOWNSAMPLED since you just wrote data
        channel = resource.get_channel()
        if channel.downsample_status.upper() == "DOWNSAMPLED":
            # Get Channel object and update status
            lookup_key = resource.get_lookup_key()
            _, exp_id, _ = lookup_key.split("&")
            channel_obj = Channel.objects.get(name=channel.name, experiment=int(exp_id))
            channel_obj.downsample_status = "NOT_DOWNSAMPLED"
            channel_obj.downsample_arn = ""
            channel_obj.save()

        # Send data to renderer
        return HttpResponse(status=201)


class Downsample(APIView):
    """
    View to handle downsample service requests

    * Requires authentication.
    """
    # Set Parser and Renderer
    parser_classes = (JSONParser, BrowsableAPIRenderer)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def get(self, request, collection, experiment, channel):
        """View to provide a channel's downsample status and properties

        Args:
            request: DRF Request object
            collection (str): Unique Collection identifier, indicating which collection you want to access
            experiment (str): Experiment identifier, indicating which experiment you want to access
            channel (str): Channel identifier, indicating which channel you want to access

        Returns:

        """
        if "iso" in request.query_params:
            if request.query_params["iso"].lower() == "true":
                iso = True
            else:
                iso = False
        else:
            iso = False

        # Process request and validate
        try:
            request_args = {
                "service": "downsample",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # Convert to Resource
        resource = project.BossResourceDjango(req)

        # Get Status
        channel = resource.get_channel()
        experiment = resource.get_experiment()
        to_renderer = {"status": channel.downsample_status}

        # Get hierarchy levels
        to_renderer["num_hierarchy_levels"] = experiment.num_hierarchy_levels

        # Gen Voxel dims
        voxel_size = {}
        voxel_dims = resource.get_downsampled_voxel_dims(iso=iso)
        for res, dims in enumerate(voxel_dims):
            voxel_size["{}".format(res)] = dims

        to_renderer["voxel_size"] = voxel_size

        # Gen Extent dims
        extent = {}
        extent_dims = resource.get_downsampled_extent_dims(iso=iso)
        for res, dims in enumerate(extent_dims):
            extent["{}".format(res)] = dims
        to_renderer["extent"] = extent

        # Get Cuboid dims
        cuboid_size = {}
        for res in range(0, experiment.num_hierarchy_levels):
            cuboid_size["{}".format(res)] = CUBOIDSIZE[res]
        to_renderer["cuboid_size"] = cuboid_size

        # Send data to renderer
        return Response(to_renderer)

    def post(self, request, collection, experiment, channel):
        """View to kick off a channel's downsample process

        Args:
            request: DRF Request object
            collection (str): Unique Collection identifier, indicating which collection you want to access
            experiment (str): Experiment identifier, indicating which experiment you want to access
            channel (str): Channel identifier, indicating which channel you want to access

        Returns:

        """
        # Process request and validate
        try:
            request_args = {
                "service": "downsample",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # Convert to Resource
        resource = project.BossResourceDjango(req)
        return start(request, resource)

    def delete(self, request, collection, experiment, channel):
        """View to cancel an in-progress downsample operation

        Args:
            request: DRF Request object
            collection (str): Unique Collection identifier, indicating which collection you want to access
            experiment (str): Experiment identifier, indicating which experiment you want to access
            channel (str): Channel identifier, indicating which channel you want to access

        Returns:

        """
        # Process request and validate
        try:
            request_args = {
                "service": "downsample",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # Convert to Resource
        resource = project.BossResourceDjango(req)

        channel = resource.get_channel()
        status = channel.downsample_status.upper()
        if status != Channel.DownsampleStatus.IN_PROGRESS and status != Channel.DownsampleStatus.QUEUED:
            return BossHTTPError("You can only cancel a queued or in-progress downsample operation.", ErrorCodes.INVALID_STATE)

        # Get Channel object
        lookup_key = resource.get_lookup_key()
        _, exp_id, chan_id = lookup_key.split("&")
        channel_obj = Channel.objects.get(name=channel.name, experiment=int(exp_id))

        session = bossutils.aws.get_session()
        if status == Channel.DownsampleStatus.IN_PROGRESS:
            # Call cancel on the Step Function
            bossutils.aws.sfn_cancel(session, channel_obj.downsample_arn, error="User Cancel",
                                     cause="User has requested the downsample operation to stop.")
        elif status == Channel.DownsampleStatus.QUEUED:
            if not delete_queued_job(session, int(chan_id)):
                return HttpResponse(status=500, reason='Could not remove job from queue')

        # Clear ARN
        channel_obj.downsample_arn = ""

        # Change Status
        channel_obj.downsample_status = Channel.DownsampleStatus.NOT_DOWNSAMPLED
        channel_obj.save()

        return HttpResponse(status=204)

class CutoutToBlack(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    # Set Parser
    parser_classes = (BloscParser, BloscPythonParser, NpygzParser, BrowsableAPIRenderer)

    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None
    
    def put(self, request, collection, experiment, channel, resolution, x_range, y_range, z_range, t_range=None):
        """
        View to handle PUT requests for a overwriting a cuboid to 0s 

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param channel: Channel identifier, indicating which dataset or annotation project you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """

        # Check for optional iso flag
        if "iso" in request.query_params:
            if request.query_params["iso"].lower() == "true":
                iso = True
            else:
                iso = False
        else:
            iso = False

        try:
            request_args = {
                "service": "cutout",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "resolution": resolution,
                "x_args": x_range,
                "y_args": y_range,
                "z_args": z_range,
                "time_args": t_range,
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # Convert to Resource
        resource = project.BossResourceDjango(req)   
        
        # Get data type
        try:
            self.bit_depth = resource.get_bit_depth()
            expected_data_type = resource.get_numpy_data_type()
        except ValueError:
            return BossHTTPError("Unsupported data type: {}".format(resource.get_data_type()), ErrorCodes.TYPE_ERROR)
    
        # Set a limit of CUTOUT_MAX_SIZE 
        if is_too_large(req, self.bit_depth):
            return BossHTTPError("Cutout overwrite is over 500MB when uncompressed. Reduce overwrite dimensions.", ErrorCodes.REQUEST_TOO_LARGE)
    
        # Get the shape of the requested data clear
        if len(req.get_time()) > 2:
            expected_shape = (len(req.get_time()), req.get_z_span(), req.get_y_span(), req.get_x_span())
        else:
            expected_shape = (req.get_z_span(), req.get_y_span(), req.get_x_span())

        # Create a binary numpy array for overwrite with specified shape and dtype
        black_cuboid = np.ones(expected_shape, dtype=expected_data_type)

        # Get interface to SPDB cache
        cache = SpatialDB(settings.KVIO_SETTINGS,
                          settings.STATEIO_CONFIG,
                          settings.OBJECTIO_CONFIG)

        # Write block to cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())

        try:
            if len(black_cuboid.shape) == 4:
                cache.write_cuboid(resource, corner, req.get_resolution(), black_cuboid, req.get_time()[0], iso=iso, to_black=True)
            else:
                cache.write_cuboid(resource, corner, req.get_resolution(),
                                   np.expand_dims(black_cuboid, axis=0), req.get_time()[0], iso=iso, to_black=True)
        except Exception as e:
            # TODO: Eventually remove as this level of detail should not be sent to the user
            log = BossLogger().logger
            log.exception('Error during write_cuboid: {}'.format(e))
            return BossHTTPError('Error during write_cuboid: {}'.format(e), ErrorCodes.BAD_REQUEST)

        # If the channel status is DOWNSAMPLED change status to NOT_DOWNSAMPLED since you just wrote data
        channel = resource.get_channel()
        if channel.downsample_status.upper() == "DOWNSAMPLED":
            # Get Channel object and update status
            lookup_key = resource.get_lookup_key()
            _, exp_id, _ = lookup_key.split("&")
            channel_obj = Channel.objects.get(name=channel.name, experiment=int(exp_id))
            channel_obj.downsample_status = "NOT_DOWNSAMPLED"
            channel_obj.downsample_arn = ""
            channel_obj.save()

        # Send data to renderer
        return HttpResponse(status=200)
