from .models import *
from .lookup import LookUpKey

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

        :param request: stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :return: Instance of BossRequest
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
        self.boss_key = None

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

        self.version = request.version
        # Parse the request for the service
        url = str(request.META['PATH_INFO'])
        m = re.match("/v(?P<version>\d+\.\d+)/(?P<service>\w+)/(?P<webargs>.*)?/?", url)

        [version, service, webargs] = [arg for arg in m.groups()]
        self.set_service(service)
        if service == 'meta':
            # The meta data service has different requirements from the cutout

            m = re.match("/?(?P<collection>\w+)/?(?P<experiment>\w+)?/?(?P<channel_layer>\w+)?/?", webargs)
            [collection_name, experiment_name, channel_layer_name] = [arg for arg in m.groups()]

            # If optional args are specified without col, experiment and dataset this is an error
            # Note this only applies to the meta service because experiment and dataset are optional
            # TODO

            self.initialize_request(request, collection_name, experiment_name, channel_layer_name)
            # TODO - Do we need this here?


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
            m = re.match(
                "/?(?P<collection>\w+)/(?P<experiment>\w+)/(?P<channel_layer>\w+)/(?P<resolution>\d)/(?P<x_range>\d+:\d+)/(?P<y_range>\d+:\d+)/(?P<z_range>\d+\:\d+)/?",
                webargs)
            if m:
                [collection_name, experiment_name, channel_layer_name, resolution, x_range, y_range, z_range] = [arg for
                                                                                                                 arg in
                                                                                                                 m.groups()]

            else:
                raise BossError(404, "Unable to parse the url.", 30000)

            self.initialize_request(request, collection_name, experiment_name, channel_layer_name)
            self.set_boss_key()
            self.set_cutoutargs(int(resolution), x_range, y_range, z_range)

    def initialize_request(self, request, collection_name, experiment_name, channel_layer_name):
        """
        Initialize the datamodel objects of the class
        :param request: stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :param collection:  Collection name from the request
        :param experiment: Experiment name from the request
        :param channel_layer_name: Channel_layer name from the request
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

        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates  (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates (eg. 100:200)
        :return: None
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

    def initialize_view_request(self, request, webargs):
        """

        :param request: DRF Request object
        :param webargs:
        :return:
        """
        print (webargs)

    def set_service(self, service):
        """
        Set the service
        :param service: service type in the request [view, meta or other]
        :return: None
        """
        self.service = service

    def set_collection(self, collection_name):
        """
        Set the current collection

        If a collection exists, get the django model and set the current collection
        :param collection: Collection name specified in the request
        :return: None
        """
        if Collection.objects.filter(name=str(collection_name)).exists():
            self.collection = Collection.objects.get(name=collection_name)
            return True
        else:
            raise BossError(404, "Collection {} not found".format(collection_name), 30000)
        return false

    def get_collection(self):
        """
        Get the collection name for the current collection
        :return: Collection name for the data model representing the current collection
        """
        if self.collection:
            return self.collection.name

    def set_experiment(self, experiment_name):
        """
        Set the current experiment

        If a experiment exists, get the django model and set the current experiment
        :param experiment: Experiment name from the request
        :return: None
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
        Get the experiment name for the current experiment
        :return: Experiment name for the data model representing the current experiment
        """

        if self.experiment:
            return self.experiment.name

    def set_channel_layer(self, channel_layer_name):
        """
        Set the current dataset

        If a dataset exists, get the django model and set the current dataset. This method also sets the current coordinate frame, default channel, default timesample and default layer if these exist for the dataset.
        :param dataset: Dataset name in the request
        :return:
        """
        if ChannelLayer.objects.filter(name=channel_layer_name, experiment=self.experiment).exists():
            self.channel_layer = ChannelLayer.objects.get(name=channel_layer_name, experiment=self.experiment)
            return True
        else:
            raise BossError(404, "Dataset {} not found".format(channel_layer_name), 30000)

    def get_channel_layer(self):
        """
        Get the curent dataset
        :return: Dataset name of the current dataset
        """
        if self.channel_layer:
            return self.channel_layer.name

    def set_key(self, key):
        """
        Set the key

        The meta key is an optional argument specified as an option argument for the metadata service
        :param key: Meta data key specified in the request
        :return: None
        """
        self.key = key

    def get_key(self):
        """
        Get the meta data key
        :return: key
        """
        return self.key

    def set_value(self, value):
        """
        Set the meta data value
        :param value: String representing the meta data
        :return:
        """
        self.value = value

    def get_value(self):
        """
        Get the string for the meta data value
        :return: value
        """
        return self.value

    def get_default_time(self):
        """
        Get the default timesample for the current dataset
        :return: Name of the default timesample
        """
        return self.default_time.name

    def get_coordinate_frame(self):
        """
        Get the coordinate with the bounds for the current dataset
        :return: Name of the coordinate frame
        """
        return self.coord_frame.name

    def get_resolution(self):
        """
        Get the resolution specified in the cutout arguments of the request
        :return: resolution
        """
        return self.resolution

    def get_x_start(self):
        """
        Get the lower X bounds specified in the cutout arguments of the request
        :return: x_start
        """
        return self.x_start

    def get_x_stop(self):
        """
        Get the upper X bounds specified in the cutout arguments of the request
        :return: x_stop
        """
        return self.x_stop

    def get_y_start(self):
        """
        Get the upper Y bounds specified in the cutout arguments of the request
        :return: Y_start
        """
        return self.y_start

    def get_y_stop(self):
        """
        Get the lower Y bounds specified in the cutout arguments of the request
        :return: Y_stop
        """
        return self.y_stop

    def get_z_start(self):
        """
        Get the upper Z bounds specified in the cutout arguments of the request
        :return: Z_stop
        """
        return self.z_start

    def get_z_stop(self):
        """
        Get the lower Z bounds specified in the cutout arguments of the request
        :return: Z_stop
        """
        return self.z_stop

    def get_x_span(self):
        """
        Get the x span for the request
        :return: x_span
        """
        return self.x_stop - self.x_start

    def get_y_span(self):
        """
        Get the Y span for the request
        :return: y_span
        """
        return self.y_stop - self.y_start

    def get_z_span(self):
        """
        Get the z span for the request
        :return:
        """
        return self.z_stop - self.z_start

    def set_boss_key(self):
        """
        Create the boss key for the request.

        The boss key concatenates the names of the datamodel stack to create a string represting the datamodel of the request
        :return: string that represents the boss key for the current request
        """

        self.boss_key = ""

        if self.collection and self.experiment and self.channel_layer:
            self.boss_key = self.collection.name + META_CONNECTOR + self.experiment.name + META_CONNECTOR + self.channel_layer.name
            return self.boss_key
        elif self.collection and self.experiment and self.service == 'meta':
            self.boss_key = self.collection.name + META_CONNECTOR + self.experiment.name
            return self.boss_key
        elif self.collection and self.service == 'meta':
            self.boss_key = self.collection.name
            return self.boss_key
        else:
            return BossHTTPError(404, "Error creating the boss key", 30000)

        return self.boss_key

    def get_boss_key(self):
        """
        Get the boss_key for the current object
        :return: boss_key
        """
        return self.boss_key

    def get_lookup_key(self):
        """

        Returns:

        """
        lookup_key = LookUpKey.get_lookup_key(self.boss_key)
        return lookup_key
