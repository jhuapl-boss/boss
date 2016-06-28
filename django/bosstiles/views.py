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

#from .parsers import BloscParser, BloscPythonParser
from .renderers import PNGImageXYRenderer, JPEGRenderer
from django.http import HttpResponse
from django.conf import settings

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, BossParserError

import spdb


class Tiles(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    # Set Parser and Renderer
    renderer_classes = JPEGRenderer,

    def get(self, request, collection, experiment, dataset, orientation, resolution, x_args, y_args, z_args):
        """
        View to handle GET requests for a cuboid of data while providing all params

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param dataset: Dataset identifier, indicating which channel or layer you want to access
        :param orientation: Integer indicating the level in the resolution hierarchy (0 = native)
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_args: Python style range indicating the X coordinates of where to post the cuboid (eg. 100:200)
        :param y_args: Python style range indicating the Y coordinates of where to post the cuboid (eg. 100:200)
        :param z_args: Python style range indicating the Z coordinates of where to post the cuboid (eg. 100:200)
        :return:
        """

        # Process request and validate
        try:
            req = BossRequest(request)
        except BossError as err:
            return BossHTTPError(err.args[0], err.args[1], err.args[2])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            self.bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossHTTPError(400, "Unsupported data type: {}".format(resource.get_data_type()))

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * self.bit_depth
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossHTTPError(413, "Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.")

        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB()

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Get a Cube instance with all time samples
        data = cache.cutout(resource, corner, extent, req.get_resolution(), [req.get_time().start, req.get_time().stop])
        #print(type(data))
        img = data.xy_image()
        # img.show()
        # import io
        # fileobj = io.BytesIO()
        # img.save(fileobj, "PNG")
        # fileobj.seek(0)
        #return fileobj.read()
        #return Response(fileobj.read(), content_type="image/png")
        # Send data to renderer
        return Response(img)

