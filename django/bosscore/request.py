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

from .models import *
from .lookup import LookUpKey
from .permissions import BossPermissionManager

import re
from .error import BossHTTPError, BossError

META_CONNECTOR = "&"


class BossRequest:
    """
    Validator for all requests that are made to the endpoint.
    """

    def __init__(self, request):
        """
        Parse the request and initalize an instance of BossRequest
        Args:
            request (stream): Django wsgi request

        Raises: BossError if the request is invalid

        """
        # Datamodel objects
        self.collection = None
        self.experiment = None
        self.channel_layer = None

        self.default_time = None
        self.coord_frame = None

        # Endpoint service and version number from the request
        self.service = None
        self.version = None

        # Boss key representing the datamodel for a valid request
        self.boss_key = []

        # Meta data key and value
        self.key = None
        self.value = None

        # Cutout args from the request
        self.resolution = None
        self.x_start = 0
        self.y_start = 0
        self.z_start = 0
        self.x_stop = 0
        self.y_stop = 0
        self.z_stop = 0

        # Timesample argument
        self.time_start = 0
        self.time_stop = 0

        # Make this private?
        self.version = request.version
        self.request = request

        # Parse the request for the service
        url = str(request.META['PATH_INFO'])

        m = re.match("/v(?P<version>\d+\.\d+)/(?P<service>\w+)/(?P<webargs>.*)?/?", url)

        [version, service, webargs] = [arg for arg in m.groups()]
        self.set_service(service)
        if service == 'meta':
            # The meta data service has different requirements from the cutout

            m = re.match("/?(?P<collection>\w+)/?(?P<experiment>\w+)?/?(?P<channel_layer>\w+)?/?", webargs)
            [collection_name, experiment_name, channel_layer_name] = [arg for arg in m.groups()]

            # If optional args are specified without col, experiment and channel this is an error
            # Note this only applies to the meta service because experiment and dataset are optional
            # TODO

            self.initialize_request(collection_name, experiment_name, channel_layer_name)

            if self.collection:
                self.set_boss_key()
                if 'key' in request.query_params:
                    self.set_key(request.query_params['key'])
                if 'value' in request.query_params:
                    self.set_value(request.query_params['value'])
            else:
                # We don't have a valid collection boss_key =""
                self.boss_key = None

        elif 'view' in request.query_params:
            raise BossError(404, "Views not implemented. Specify the full request", 30000)
        else:
            m = re.match("/?(?P<collection>\w+)/(?P<experiment>\w+)/(?P<channel_layer>\w+)/(?P<resolution>\d)/"
                         + "(?P<x_range>\d+:\d+)/(?P<y_range>\d+:\d+)/(?P<z_range>\d+\:\d+)/?(?P<rest>.*)?/?", webargs)

            if m:
                [collection_name, experiment_name, channel_layer_name, resolution, x_range, y_range, z_range] \
                    = [arg for arg in m.groups()[:-1]]
                time = m.groups()[-1]
                self.initialize_request(collection_name, experiment_name, channel_layer_name)
                if not time:
                    # get default time
                    self.time_start = self.channel_layer.default_time_step
                    self.time_stop = self.channel_layer.default_time_step + 1
                else:
                    self.set_time(time)

                self.set_boss_key()
                self.set_cutoutargs(int(resolution), x_range, y_range, z_range)
            else:
                raise BossError(404, "Unable to parse the url.", 30000)

    def initialize_request(self, collection_name, experiment_name, channel_layer_name):
        """
        Initialize the datamodel objects of the class

        Args:
            collection_name: Collection name from the request
            experiment_name: Experiment name from the request
            channel_layer_name: Channel_layer name from the request

        """
        if collection_name:
            colstatus = self.set_collection(collection_name)
            if experiment_name and colstatus:
                expstatus = self.set_experiment(experiment_name)
                if channel_layer_name and expstatus:
                    self.set_channel_layer(channel_layer_name)

    def set_cutoutargs(self, resolution, x_range, y_range, z_range):
        """
        Validate and initialize cutout arguments from the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            x_range: Python style range indicating the X coordinates  (eg. 100:200)
            y_range: Python style range indicating the Y coordinates (eg. 100:200)
            z_range: Python style range indicating the Z coordinates (eg. 100:200)

        Returns:

        """
        if resolution in range(0, self.experiment.num_hierarchy_levels):
            self.resolution = int(resolution)

        # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

        x_coords = x_range.split(":")
        y_coords = y_range.split(":")
        z_coords = z_range.split(":")

        try:
            self.x_start = int(x_coords[0])
            self.x_stop = int(x_coords[1])

            self.y_start = int(y_coords[0])
            self.y_stop = int(y_coords[1])

            self.z_start = int(z_coords[0])
            self.z_stop = int(z_coords[1])

            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop):
                raise BossError(404,
                                "Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_range, y_range, z_range),
                                30000)

        except TypeError:
            raise BossError(404,
                            "Type error in cutout argument{}/{}/{}/{}".format(resolution, x_range, y_range, z_range),
                            30000)

    def initialize_view_request(self, webargs):
        """
        Function to handle views
        Args:
            webargs:

        Returns:

        """
        print (webargs)

    def set_service(self, service):
        """
        Set the service  variable. The service can be meta, view or cutout
        Args:
            service: service requested in the request

        Returns: None

        """
        self.service = service

    def set_collection(self, collection_name):
        """
        Validate the collection and set collection object.
        Args:
            collection_name: Collection name from the request

        Returns:None

        Raises : BossError is the collection is not found.

        """
        if Collection.objects.filter(name=str(collection_name)).exists():
            self.collection = Collection.objects.get(name=collection_name)
            return True
        else:
            raise BossError(404, "Collection {} not found".format(collection_name), 30000)

    def get_collection(self):
        """
        Get the collection name for the current collection
        Returns:

        """
        if self.collection:
            return self.collection.name

    def set_experiment(self, experiment_name):
        """
        Validate and set the experiment
        Args:
            experiment_name: Experiment name from the request

        Returns: BossError is the experiment with the matching name is not found in the db

        """
        if Experiment.objects.filter(name=experiment_name, collection=self.collection).exists():
            self.experiment = Experiment.objects.get(name=experiment_name, collection=self.collection)
            self.coord_frame = self.experiment.coord_frame
            return True
        else:
            raise BossError(404, "Experiment {} not found".format(experiment_name), 30000)

        return false

    def get_experiment(self):
        """
        Return the experiment name for the current experiment

        Returns:
            self.experiment.name (str): Experiment name for the data model representing the current experiment

        """
        if self.experiment:
            return self.experiment.name

    def set_channel_layer(self, channel_layer_name):
        """
        Validate and set the channel or layer
        Args:
            channel_layer_name: Channel or layer name specified in the request

        Returns:

        """
        if ChannelLayer.objects.filter(name=channel_layer_name, experiment=self.experiment).exists():
            self.channel_layer = ChannelLayer.objects.get(name=channel_layer_name, experiment=self.experiment)
            return True
        else:
            raise BossError(404, "Dataset {} not found".format(channel_layer_name), 30000)

    def get_channel_layer(self):
        """
        Return the channel or layer name for the channel or layer

        Returns:
            self.channel_layer.name (str) : Name of channel or layer

        """
        if self.channel_layer:
            return self.channel_layer.name

    def set_key(self, key):
        """
        Set the meta data key. This is an optional argument used by the metadata service
        Args:
            key: Meta data key specified in the request

        """
        self.key = key

    def get_key(self):
        """
        Return the meta data key
        Returns:
            self.key (str) : Metadata key

        """
        return self.key

    def set_value(self, value):
        """
        Set the meta data value. This is an optional argument used by the metadata service
        Args:
            value: String representing the meta data value

        """
        self.value = value

    def get_value(self):
        """
        Return the value associated with the metadata
        Returns:
            self.value (str) : Meta data value

        """
        return self.value

    def get_default_time(self):
        """
        Return the default timesample for the channel or layer
        Returns:
            self.default_time (int) : Default timestep for the channel or layer

        """
        return self.default_time

    def get_coordinate_frame(self):
        """
        Returns the coordinate frame for the experiment
        Returns:
            self.coord_frame.name (str) : Name of coordinate frame

        """
        return self.coord_frame.name

    def get_resolution(self):
        """
        Return the resolution specified in the cutout arguments of the request
        Returns:
            self.resolution (int) : Resolution

        """
        return self.resolution

    def get_x_start(self):
        """
        Return the lower X bounds for the request
        Returns:
            self.x_start(int) : Lower bounds for X range

        """
        return self.x_start

    def get_x_stop(self):
        """
        Return the upper X bounds specified in the cutout arguments

        Returns:
            self.x_stop (int) : Upper bounds for X range
        """
        return self.x_stop

    def get_y_start(self):
        """
        Get the lower Y bounds specified in the cutout arguments of the request
        Returns:
            self.y_start (int) : lower bounds for Y range
        """
        return self.y_start

    def get_y_stop(self):
        """
        Get the upper Y bounds specified in the cutout arguments of the request
        Returns:
            self.y_stop (int) : Upper bounds for Y range
        """
        return self.y_stop

    def get_z_start(self):
        """
        Get the lower Z bounds specified in the cutout arguments of the request
        Returns:
            self.z_start (int) :  Lower bounds for Z range
        """
        return self.z_start

    def get_z_stop(self):
        """
        Get the lower Z bounds specified in the cutout arguments of the request
        Returns:
             self.z_stop (int) : Upper bounds for Z range
        """
        return self.z_stop

    def get_x_span(self):
        """
        Get the x span for the request
        Returns:
            x_span (int) : X span
        """
        return self.x_stop - self.x_start

    def get_y_span(self):
        """
        Get the Y span for the request
        Returns:
            y_span (int) : Y span
        """
        return self.y_stop - self.y_start

    def get_z_span(self):
        """
        Get the z span for the request
        Returns:
            z_span (int): Z span
        """
        return self.z_stop - self.z_start

    def set_boss_key(self):
        """
        Create the boss key for the request.

        The boss key concatenates the names of the datamodel stack to create a string represting the request
        Returns:
            self.bosskey(str) : String that represents the boss key for the current request
        """
        boss_key = []

        if self.collection and self.experiment and self.channel_layer:
            boss_key = self.collection.name + META_CONNECTOR + self.experiment.name + META_CONNECTOR + self.channel_layer.name
            #   perm = BossPermissionManager.check_permissions_object(self.request.user,self.channel_layer,
            #                                                      self.request.method,'channellayer')
        elif self.collection and self.experiment and self.service == 'meta':
            boss_key = self.collection.name + META_CONNECTOR + self.experiment.name
            #perm = BossPermissionManager.check_permissions_object(self.request.user,self.experiment,
            #                                                      self.request.method,'experiment')
        elif self.collection and self.service == 'meta':
            boss_key = self.collection.name
            #perm = BossPermissionManager.check_permissions_object(self.request.user,self.collection,
            #                                                      self.request.method,'collection')
        else:
            return BossHTTPError(404, "Error creating the boss key", 30000)

        #if not perm:
        #    return BossHTTPError(404, "You do not have permissions", 30000)

        self.boss_key = []
        if self.service == 'meta':
            self.boss_key.append(boss_key)
        else:
            for time_step in range(self.time_start, self.time_stop):
                key = boss_key + '&' + str(time_step)
                self.boss_key.append(key)

        return self.boss_key


    def get_boss_key(self):
        """
        Get the boss_key for the current object

        Returns:
            self.boss_key (str) : Boss key
        """
        return self.boss_key

    def get_lookup_key(self):
        """
        Returns the lookup kefor the request

        Returns:
            lookup (list(str))) : List of Lookup keys that correspond to the request

        """
        lookup = []
        for key in self.boss_key:
            lkey = LookUpKey.get_lookup_key(key)
            if lkey:
                lookup.append(lkey.lookup_key)
        return lookup

    def set_time(self, time):
        """
        Set the time range for a request.
        Args:
            time: String representing the Time range

        Raises : Boss Error if the range is out or bounds or invalid

        """
        m = re.match("/?(?P<time_start>\d+)\:?(?P<time_stop>\d+)?/?", time)
        if m:
            [tstart, tstop] = [arg for arg in m.groups()]
            if tstart:
                self.time_start = int(tstart)
                if self.time_start > self.experiment.max_time_sample:
                    return BossHTTPError(404, "Invalid time range {}. Start time is greater than the maximum time "
                                              "sample {}".format(time, str(self.experiment.max_time_sample)), 30000)
            else:
                return BossHTTPError(404, "Unable to parse time sample argument {}".format(time), 30000)
            if tstop:
                self.time_stop = int(tstop)
                if self.time_stop > self.time_start or self.time_stop > self.experiment.max_time_sample + 1:
                    return BossHTTPError(404, "Invalid time range {}. End time is greater than the start time "
                                              "or out of bouds with maximum time sample {}".format(time, str(
                        self.experiment.max_time_sample)), 30000)
            else:
                self.time_stop = self.time_start + 1

    def get_time(self):
        """
        Return the time step range
        Returns:
            Time sample range

        """
        return range(self.time_start, self.time_stop)
