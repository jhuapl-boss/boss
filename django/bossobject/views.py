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

from bosscore.request import BossRequest
from bosscore.error import BossError, BossHTTPError, ErrorCodes

from spdb.spatialdb.spatialdb import SpatialDB
from spdb import project

from django.conf import settings


class Reserve(APIView):
    """
        View to reserve annotation object ids

    """
    def get(self, request, collection, experiment, channel, num_ids):
        """
        Reserve a unique, sequential list of annotation ids for the provided channel to use as
        object ids for annotations.

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment
            channel: Channel_name
            num_ids: Number of id you want to reserve
        Returns:
            JSON dict with start_id and count of ids reserved
        Raises:
            BossHTTPError for an invalid request
        """

        # validate resource
        # permissions?
        # validate that num_ids is an int
        # Check if this is annotation channel

        try:
            request_args = {
                "service": "reserve",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # create a resource
        resource = project.BossResourceDjango(req)
        try:
            # Reserve ids
            spdb = SpatialDB(settings.KVIO_SETTINGS, settings.STATEIO_CONFIG, settings.OBJECTIO_CONFIG)
            start_id = spdb.reserve_ids(resource, int(num_ids))
            data = {'start_id': start_id[0], 'count': num_ids}
            return Response(data, status=200)
        except (TypeError, ValueError)as e:
            return BossHTTPError("Type error in the reserve id view. {}".format(e), ErrorCodes.TYPE_ERROR)


class Ids(APIView):
    """
        View to get the ids of all the annotation objects in a spatial region

    """
    def get(self, request, collection, experiment,channel, resolution, x_range, y_range, z_range, t_range=None):
        """
        Return a list of ids in the spatial region.

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment
            channel: Channel_name
            num_ids: Number of id you want to reserve
        Returns:
            JSON dict with start_id and count of ids reserved
        Raises:
            BossHTTPError for an invalid request
        """

        # validate resource
        # permissions?
        # Check if this is annotation channel
        # Process request and validate
        try:
            request_args = {
                "service": "ids",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "resolution": resolution,
                "x_args": x_range,
                "y_args": y_range,
                "z_args": z_range,
                "time_args": t_range
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # create a resource
        resource = project.BossResourceDjango(req)

        # Get the params to pull data out of the cache
        corner = (req.get_x_start(), req.get_y_start(), req.get_z_start())
        extent = (req.get_x_span(), req.get_y_span(), req.get_z_span())

        try:
            # Reserve ids
            spdb = SpatialDB(settings.KVIO_SETTINGS, settings.STATEIO_CONFIG, settings.OBJECTIO_CONFIG)
            ids = spdb.get_ids_in_region(resource, int(resolution), corner, extent)
            return Response(ids, status=200)
        except (TypeError, ValueError) as e:
            return BossHTTPError("Type error in the ids view. {}".format(e), ErrorCodes.TYPE_ERROR)


class BoundingBox(APIView):
    """
        View to reserve annotation object ids

    """
    def get(self, request, collection, experiment, channel, resolution, id):
        """
        Return the bounding box containing the object

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment
            channel: Channel_name
            resolution: Data resolution
            id: The id of the object
        Returns:
            JSON dict with the bounding box of the object
        Raises:
            BossHTTPError for an invalid request
        """

        # validate resource
        # permissions?
        # validate that id is an int
        # Check if this is annotation channel

        if 'type' in request.query_params:
            bb_type = request.query_params['type']
            if bb_type != 'loose' and bb_type != 'tight':
                return BossHTTPError("Invalid option for bounding box type {}. The valid options are : loose or tight"
                                     .format(bb_type), ErrorCodes.INVALID_ARGUMENT)
        else:
            bb_type = 'loose'

        try:
            request_args = {
                "service": "boundingbox",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "resolution": resolution,
                "id": id
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # create a resource
        resource = project.BossResourceDjango(req)

        try:
            # Get interface to SPDB cache
            spdb = SpatialDB(settings.KVIO_SETTINGS, settings.STATEIO_CONFIG, settings.OBJECTIO_CONFIG)
            data = spdb.get_bounding_box(resource, int(resolution), int(id), bb_type=bb_type)
            if data is None:
                return BossHTTPError("The id does not exist. {}".format(id), ErrorCodes.OBJECT_NOT_FOUND)
            return Response(data, status=200)
        except (TypeError, ValueError) as e:
            return BossHTTPError("Type error in the boundingbox view. {}".format(e), ErrorCodes.TYPE_ERROR)


class CuboidsFromID(APIView):
    """
        View to get cuboids that belong to a certain ID. 

    """
    def get(self, request, collection, experiment, channel, resolution, id):
        """
        Return the list of cuboid indicies that belong to a certain ID. 

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment
            channel: Channel_name
            resolution: Data resolution
            id: The id of the object
        Returns:
            JSON dict with the list of cuboid indicies. 
        Raises:
            BossHTTPError for an invalid request
        """

        try:
            request_args = {
                "service": "boundingbox",
                "collection_name": collection,
                "experiment_name": experiment,
                "channel_name": channel,
                "resolution": resolution,
                "id": id
            }
            req = BossRequest(request, request_args)
        except BossError as err:
            return err.to_http()

        # create a resource
        resource = project.BossResourceDjango(req)

        try:
            # Get interface to SPDB cache
            spdb = SpatialDB(settings.KVIO_SETTINGS, settings.STATEIO_CONFIG, settings.OBJECTIO_CONFIG)
            data = spdb.get_cuboids_from_id(resource, int(resolution), int(id))
            if data is None:
                return BossHTTPError("The id does not exist. {}".format(id), ErrorCodes.OBJECT_NOT_FOUND)
            return Response(data, status=200)
        except (TypeError, ValueError) as e:
            return BossHTTPError("Type error in the CuboidsFromIDs view. {}".format(e), ErrorCodes.TYPE_ERROR)