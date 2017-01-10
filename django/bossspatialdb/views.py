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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from .parsers import BloscParser, BloscPythonParser
from .renderers import BloscRenderer, BloscPythonRenderer

from django.http import HttpResponse
from django.conf import settings

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, BossParserError, ErrorCodes

from spdb.spatialdb.spatialdb import SpatialDB
from spdb import project


class Cutout(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    # Set Parser and Renderer
    parser_classes = (BloscParser, BloscPythonParser)
    renderer_classes = (BloscRenderer, BloscPythonRenderer, JSONRenderer, BrowsableAPIRenderer)

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
            ids = request.query_params[filter]
        else:
            ids = None

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

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * (self.bit_depth / 8)
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossHTTPError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                 ErrorCodes.REQUEST_TOO_LARGE)

        # Get interface to SPDB cache
        cache = SpatialDB(settings.KVIO_SETTINGS,
                          settings.STATEIO_CONFIG,
                          settings.OBJECTIO_CONFIG)

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Get a Cube instance with all time samples
        data = cache.cutout(resource, corner, extent, req.get_resolution(), [req.get_time().start, req.get_time().stop],
                            filter_ids = req.get_filter_ids())
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

        # Get interface to SPDB cache
        cache = SpatialDB(settings.KVIO_SETTINGS,
                          settings.STATEIO_CONFIG,
                          settings.OBJECTIO_CONFIG)

        # Write block to cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())

        try:
            if len(request.data[2].shape) == 4:
                cache.write_cuboid(resource, corner, req.get_resolution(), request.data[2], req.get_time()[0])
            else:
                cache.write_cuboid(resource, corner, req.get_resolution(),
                                   np.expand_dims(request.data[2], axis=0), req.get_time()[0])
        except Exception as e:
            # TODO: Eventually remove as this level of detail should not be sent to the user
            return BossHTTPError('Error during write_cuboid: {}'.format(e), ErrorCodes.BOSS_SYSTEM_ERROR)

        # Send data to renderer
        return HttpResponse(status=201)

