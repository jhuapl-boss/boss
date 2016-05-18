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
from rest_framework import authentication, permissions
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from .parsers import BloscParser, BloscPythonParser
from .renderers import BloscRenderer, BloscPythonRenderer

from django.http import HttpResponse

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError

import spdb


class Cutout(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    # Set Parser and Renderer

    parser_classes = (BloscParser, BloscPythonParser)
    renderer_classes = (BloscRenderer, BloscPythonRenderer, BrowsableAPIRenderer)

    def get(self, request, collection, experiment, dataset, resolution, x_range, y_range, z_range):
        """
        View to handle GET requests for a cuboid of data while providing all params

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param dataset: Dataset identifier, indicating which channel or layer you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """
        # Process request and validate
        try:
            req = BossRequest(request)
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Make sure datatype is valid
        self.data_type = resource.get_data_type()
        if self.data_type == "uint8":
            self.bit_depth = 8
        elif self.data_type == "uint16":
            self.bit_depth = 16
        elif self.data_type == "uint64":
            self.bit_depth = 64
        else:
            return BossHTTPError(400, "Unsupported datatype provided to parser")

        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB()

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Get a Cube instance with all time samples
        data = cache.cutout(resource, corner, extent, req.get_resolution(), [req.get_time().start, req.get_time().stop])

        # Send data to renderer
        return Response(data)

    def post(self, request, collection, experiment, dataset, resolution, x_range, y_range, z_range):
        """
        View to handle POST requests for a cuboid of data while providing all datamodel params

        Due to parser implementation, request.data should be a numpy array already.

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param dataset: Dataset identifier, indicating which dataset or annotation project you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """
        # Process request and validate
        try:
            req = BossRequest(request)
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB()

        # Write block to cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())

        try:
            cache.write_cuboid(resource, corner, req.get_resolution(), request.data, req.get_time()[0])
        except BaseException as e:
            return BossHTTPError(500, 'Error during write_cuboid: ' + str(e))

        # Send data to renderer
        return HttpResponse(status=201)

