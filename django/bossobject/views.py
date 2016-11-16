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


class Reserve(APIView):
    """
        View to reserve annotation object ids

    """
    def get(self, request, collection, experiment,channel, num_ids):
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

        data = {"start_id": 1000, "count": 1000}
        return Response(data, status=200)


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

        data = {"ids": ["1", "2", "3", "4", "5"]}
        return Response(data, status=200)

class BoundingBox(APIView):
    """
        View to reserve annotation object ids

    """
    def get(self, request, collection, experiment,channel, id):
        """
        Return the bounding box containing the object

        Args:
            request: DRF Request object
            collection: Collection name specifying the collection you want
            experiment: Experiment name specifying the experiment
            channel: Channel_name
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

        data = {"x_range": [0,1000], "y_range": [0,1000], "z_range": [0,1000], "t_range":[0,10]}
        return Response(data, status=200)
