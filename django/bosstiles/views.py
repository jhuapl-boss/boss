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

from django.http import HttpResponse
from django.conf import settings

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, ErrorCodes

import spdb

from .renderers import PNGRenderer, JPEGRenderer


class Image(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires authentication.
    """
    renderer_classes = (PNGRenderer, JPEGRenderer)

    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    def get(self, request, collection, experiment, dataset, orientation, resolution, x_args, y_args, z_args):
        """
        View to handle GET requests for a cuboid of data while providing all params

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param dataset: Dataset identifier, indicating which channel or layer you want to access
        :param orientation: Image plane requested. Vaid options include xy,xz or yz
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
            return BossHTTPError(err[0], err[1])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            self.bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossHTTPError("Datatype does not match channel/layer", ErrorCodes.DATATYPE_DOES_NOT_MATCH)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * (self.bit_depth/8)
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossHTTPError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                 ErrorCodes.REQUEST_TOO_LARGE)

        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB(settings.KVIO_SETTINGS,
                                         settings.STATEIO_CONFIG,
                                         settings.OBJECTIO_CONFIG)

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        # Do a cutout as specified
        data = cache.cutout(resource, corner, extent, req.get_resolution(),
                            [req.get_time().start, req.get_time().stop])

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
    def __init__(self):
        super().__init__()
        self.data_type = None
        self.bit_depth = None

    def get(self, request, collection, experiment, dataset, orientation, tile_size, resolution, x_idx, y_idx, z_idx, t_idx=None):
        """
        View to handle GET requests for a tile when providing indices. Currently only supports XY plane

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param collection: Unique Collection identifier, indicating which collection you want to access
        :param experiment: Experiment identifier, indicating which experiment you want to access
        :param dataset: Dataset identifier, indicating which channel or layer you want to access
        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_idx: the tile index in the X dimension
        :param y_idx: the tile index in the Y dimension
        :param z_idx: the tile index in the Z dimension
        :param t_idx: the tile index in the T dimension
        :return:
        """
        # Process request and validate
        try:
            req = BossRequest(request)
        except BossError as err:
            return BossHTTPError(err[0], err[1])

        # Convert to Resource
        resource = spdb.project.BossResourceDjango(req)

        # Get bit depth
        try:
            self.bit_depth = resource.get_bit_depth()
        except ValueError:
            return BossHTTPError("Datatype does not match channel/layer", ErrorCodes.DATATYPE_DOES_NOT_MATCH)

        # Make sure cutout request is under 1GB UNCOMPRESSED
        total_bytes = req.get_x_span() * req.get_y_span() * req.get_z_span() * len(req.get_time()) * (self.bit_depth/8)
        if total_bytes > settings.CUTOUT_MAX_SIZE:
            return BossHTTPError("Cutout request is over 1GB when uncompressed. Reduce cutout dimensions.",
                                 ErrorCodes.REQUEST_TOO_LARGE)

        # Get interface to SPDB cache
        cache = spdb.spatialdb.SpatialDB(settings.KVIO_SETTINGS,
                                         settings.STATEIO_CONFIG,
                                         settings.OBJECTIO_CONFIG)

        # Get the params to pull data out of the cache
        if orientation == 'xy':
            corner = (tile_size * x_idx, tile_size * y_idx, z_idx)
            extent = (tile_size * (x_idx + 1), tile_size * (y_idx + 1), z_idx)
        elif orientation == 'yz':
            corner = (x_idx, tile_size * y_idx, tile_size * z_idx)
            extent = (x_idx, tile_size * (y_idx + 1), tile_size * (z_idx + 1))
        elif orientation == 'xz':
            corner = (tile_size * x_idx, y_idx, tile_size * z_idx)
            extent = (tile_size * (x_idx + 1), y_idx, tile_size * (z_idx + 1))
        else:
            return BossHTTPError("Invalid orientation: {}".format(orientation),
                                 ErrorCodes.INVALID_CUTOUT_ARGS)

        # Do a cutout as specified
        data = cache.cutout(resource, corner, extent, req.get_resolution(),
                            [req.get_time().start, req.get_time().stop])

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

