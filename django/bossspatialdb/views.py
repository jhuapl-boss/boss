from django.shortcuts import render
from django.http import HttpResponse
from django.http import Http404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
import blosc
import numpy as np

from .parsers import BloscParser

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError


class Cutout(APIView):
    """
    View to handle spatial cutouts by providing all datamodel fields

    * Requires token authentication.
    """
    # TODO: add auth and permissions once user stuff is setup, currently allowing everyone and now auth
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    # Set Parser and Renderer
    # TODO: Look into using a renderer, so you can send data back in multiple formats
    parser_classes = (BloscParser,)

    def read_cutout(self, request):
        """
        Method to get a cuboid of data from spdb

        :param request: BossRequest
        :return:
        """
        # Get bitdepth of dataset
        # TODO: Query for datatype
        numbytes = 8

        # Get Cutout
        # TODO: Call spdb to get cubes
        cutout = np.random.random((request.get_x_span(), request.get_y_span(), request.get_z_span()))

        # Compress and return
        return blosc.compress(cutout, typesize=numbytes)

    def write_cutout(self, data, request):
        '''
        Method to write a cutout of data to spdb interface

        :param data:
        :param request: BossRequest
        :return:
        '''

        # Get bitdepth of dataset
        # TODO: Query for dtype based on datatype of layer
        datatype = int

        # Format data
        # TODO: Query for dtype based on datatype of layer
        data_mat = np.fromstring(data, dtype=datatype)
        print(request.get_x_span())
        print(request.get_y_span())
        print(request.get_z_span())
        data_mat = np.reshape(data_mat, (request.get_x_span(), request.get_y_span(), request.get_z_span()), order='C')

        # Dice into cuboids
        # TODO: Dice data into cuboids

        # Write to cache
        # TODO: Write data to cache
        print("Would have written {0} bytes to the cache".format(len(data)))

    def get(self, request, collection, experiment, dataset, resolution, x_range, y_range, z_range):
        """
        View to handle GET requests for a cuboit of data while providing all params

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

        # Get Cutout
        d = self.read_cutout(req)

        return HttpResponse(d, content_type='application/octet-stream', status=200)

    def post(self, request, collection, experiment, dataset, resolution, x_range, y_range, z_range):
        """
        View to handle POST requests for a cuboid of data while providing all datamodel params

        Cuboid data should be LZ4 compressed bytes

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

        # Write byte array to spdb interface after reshape and cutout
        self.write_cutout(request.data, req)

        return Response(status=201)


class CutoutView(Cutout):
    """
    View to handle spatial cutouts by providing a datamodel view token
    """

    def get(self, request, resolution, x_range, y_range, z_range):
        """
        GET an arbitrary cutout of data based on a datamodel view token

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param view: Unique View identifier, indicating which collection, experiment, and dataset you want to access
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

        # Get Cutout
        d = self.read_cutout(req)

        return HttpResponse(d, content_type='application/octet-stream', status=200)

    def post(self, request, resolution, x_range, y_range, z_range):
        """
        View to handle POST requests for a cuboid of data while providing all datamodel params

        Cuboid data should be LZ4 compressed bytes

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :param view: Unique View identifier, indicating which collection, experiment, and dataset you want to access
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

        # Write byte array to spdb interface after reshape and cutout
        self.write_cutout(request.data, req)

        return Response(status=201)

