from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
import blosc
import numpy as np

from .parsers import BloscParser


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

    def read_cutout(self, collection, experiment, dataset, resolution, x_range, y_range, z_range,
                    channel=None, time=None, layer=None):
        '''
        Method to get a cuboid of data from spdb

        :param collection:
        :param experiment:
        :param dataset:
        :param resolution:
        :param x_range:
        :param y_range:
        :param z_range:
        :param channel:
        :param time:
        :param layer:
        :return:
        '''
        # TODO: Validate resolution, xyz range, optional args
        x_coords = x_range.split(":")
        y_coords = y_range.split(":")
        z_coords = z_range.split(":")
        x_span = int(x_coords[1]) - int(x_coords[0])
        y_span = int(y_coords[1]) - int(y_coords[0])
        z_span = int(z_coords[1]) - int(z_coords[0])

        # Set Channel
        if channel:
            channel_val = channel
        else:
            #TODO: Set to default channel
            channel_val = 'default'

        # Set Timepoint
        if time:
            time_val = time
        else:
            #TODO: Set to default time
            time_val = 'default'

        # Set layer
        if layer:
            layer_val = layer
        else:
            #TODO: Set to default layer
            layer_val = 'default'

        # Get bitdepth of dataset
        # TODO: Query for datatype
        numbytes = 8

        # Get Cutout
        # TODO: Call spdb to get cubes
        cutout = np.random.random((x_span, y_span, z_span))

        # Compress and return
        return blosc.compress(cutout, typesize=numbytes)

    def write_cutout(self, data, collection, experiment, dataset, resolution, x_range, y_range, z_range,
                     channel=None, time=None, layer=None):
        '''
        Method to write a cutout of data to spdb interface

        :param data:
        :param collection:
        :param experiment:
        :param dataset:
        :param resolution:
        :param x_range:
        :param y_range:
        :param z_range:
        :param channel:
        :param time:
        :param layer:
        :return:
        '''
        # TODO: Validate resolution, xyz range, optional args
        x_coords = x_range.split(":")
        y_coords = y_range.split(":")
        z_coords = z_range.split(":")
        x_span = int(x_coords[1]) - int(x_coords[0])
        y_span = int(y_coords[1]) - int(y_coords[0])
        z_span = int(z_coords[1]) - int(z_coords[0])

        # Set Channel
        if channel:
            channel_val = channel
        else:
            #TODO: Set to default channel
            channel_val = 'default'

        # Set Timepoint
        if time:
            time_val = time
        else:
            #TODO: Set to default time
            time_val = 'default'

        # Set layer
        if layer:
            layer_val = layer
        else:
            #TODO: Set to default layer
            layer_val = 'default'

        # Get bitdepth of dataset
        # TODO: Query for dtype based on datatype of layer
        datatype = int

        # Format data
        # TODO: Query for dtype based on datatype of layer
        data_mat = np.fromstring(data, dtype=datatype)
        data_mat = np.reshape(data_mat, (x_span, y_span, z_span), order='C')

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

        # Set Channel
        if 'ch' in request.query_params:
            channel = request.query_params['ch']
        else:
            channel = None

        # Set Timepoint
        if 'time' in request.query_params:
            time = request.query_params['time']
        else:
            time = None

        # Set Layer
        if 'layer' in request.query_params:
            layer = request.query_params['layer']
        else:
            layer = None

        # Get Cutout
        d = self.read_cutout(collection, experiment, dataset, resolution,
                             x_range, y_range, z_range, channel, time, layer)

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
        # Set Channel
        if 'ch' in request.query_params:
            channel = request.query_params['ch']
        else:
            channel = None

        # Set Timepoint
        if 'time' in request.query_params:
            time = request.query_params['time']
        else:
            time = None

        # Set Layer
        if 'layer' in request.query_params:
            layer = request.query_params['layer']
        else:
            layer = None

        # Write byte array to spdb interface after reshape and cutout
        self.write_cutout(request.data, collection, experiment, dataset, resolution,
                          x_range, y_range, z_range, channel, time, layer)

        return Response(status=201)


class CutoutView(Cutout):
    """
    View to handle spatial cutouts by providing a datamodel view token
    """

    def lookup_view(self, view):
        """
        Method to lookup a view token and return the collection, experiment, and project

        :param view: Unique View string token
        :type view: str
        :returns: List containing the collection, exp, and proj
        :rtype: list
        """
        # TODO: Lookup the col,exp,proj based on the view

        return ['col1', 'exp1', 'proj1']

    def get(self, request, view, resolution, x_range, y_range, z_range, format=None):
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
        # Lookup view
        tokens = self.lookup_view(view)

        # Set Channel
        if 'ch' in request.query_params:
            channel = request.query_params['ch']
        else:
            channel = None

        # Set Time Point
        if 'time' in request.query_params:
            time = request.query_params['time']
        else:
            time = None

        # Set Layer
        if 'layer' in request.query_params:
            layer = request.query_params['layer']
        else:
            layer = None

        # Get Cutout
        d = self.read_cutout(tokens[0], tokens[1], tokens[2], resolution,
                             x_range, y_range, z_range, channel, time, layer)

        return HttpResponse(d, content_type='application/octet-stream', status=200)

    def post(self, request, view, resolution, x_range, y_range, z_range):
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
        # Lookup view
        tokens = self.lookup_view(view)

        # Set Channel
        if 'ch' in request.query_params:
            channel = request.query_params['ch']
        else:
            channel = None

        # Set Timepoint
        if 'time' in request.query_params:
            time = request.query_params['time']
        else:
            time = None

        # Set Layer
        if 'layer' in request.query_params:
            layer = request.query_params['layer']
        else:
            layer = None

        # Write byte array to spdb interface after reshape and cutout
        self.write_cutout(request.data, tokens[0], tokens[1], tokens[2], resolution,
                          x_range, y_range, z_range, channel, time, layer)

        return Response(status=201)

