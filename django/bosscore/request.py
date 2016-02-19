from .models import *
from django.http import HttpResponse
from urllib.error import HTTPError

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
        self.collectionobj = None
        self.experimentobj = None
        self.datasetobj = None
        self.channelobj = None
        self.timesampleobj = None
        self.layerobj = None
        self.default_channel = None
        self.default_time = None
        self.default_layer = None
        self.coord_frame = None

        # Endpoint service and version number from the request
        self.service = None
        self.version = None

        # Boss key representing the datamodel for a valid request
        self.bosskey = None

        # Meta data key and value
        self.metakey = None
        self.metavalue = None

        # Cutout args from the request
        self.resolution = None
        self.x_start = 0
        self.y_start = 0
        self.z_start = 0
        self.x_stop = 0
        self.y_stop = 0
        self.z_stop = 0

        # Parse the request for the service
        url = str(request.META['PATH_INFO'])
        m = re.match("/v(?P<version>\d+\.\d+)/(?P<service>\w+)/(?P<webargs>.*)?/?", url)

        [version, service, webargs] = [arg for arg in m.groups()]
        self.set_service(service)
        self.version = version

        if service == 'meta':
            # The meta data service has different requirements from the cutout

            m = re.match("/?(?P<collection>\w+)/?(?P<experiment>\w+)?/?(?P<dataset>\w+)?/?", webargs)
            [collection, experiment, dataset] = [arg for arg in m.groups()]

            # If optional args are specified without col, experiment and dataset this is an error
            # Note this only applies to the meta service because experiment and dataset are optional
            # TODO

            self.initialize_request(request, collection, experiment, dataset)
            # TODO - Do we need this here?
            if self.collectionobj:
                self.set_bosskey()
                if 'metakey' in request.query_params:
                    self.set_metakey(request.query_params['metakey'])
                if 'metavalue' in request.query_params:
                    self.set_metavalue(request.query_params['metavalue'])
            else:
                # We don't have a valid collection bosskey =""
                self.bosskey = None

        elif 'view' in request.query_params:
            raise BossError(404, "Views not implemented. Specify the full request", 30000)
        else:
            m = re.match(
                "/?(?P<collection>\w+)/(?P<experiment>\w+)/(?P<dataset>\w+)/(?P<resolution>\d)/(?P<x_range>\d+:\d+)/(?P<y_range>\d+:\d+)/(?P<z_range>\d+\:\d+)/?",
                webargs)
            if (m):
                [collection, experiment, dataset, resolution, x_range, y_range, z_range] = [arg for arg in m.groups()]

            else:
                raise BossError(404, "Request does not match", 30000)

            self.initialize_request(request, collection, experiment, dataset)
            self.set_bosskey()
            self.set_cutoutargs(int(resolution), x_range, y_range, z_range)

    def initialize_request(self, request, collection, experiment, dataset):
        """
        Initialize the datamodel objects of the class
        :param request: stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :param collection:  Collection name from the request
        :param experiment: Experiment name from the request
        :param dataset: Dataset name from the request
        """
        if collection:
            colstatus = self.set_collection(collection)
            if experiment and colstatus:
                expstatus = self.set_experiment(experiment)
                if dataset and expstatus:
                    dsstatus = self.set_dataset(dataset)
                    if self.service == 'meta':
                        self.initialize_optargs_meta(request)
                    else:
                        self.initialize_optargs(request)

    def initialize_optargs(self, request):
        """
        Validate and initialize optional arguments for the datamodel

        The optional arguments for the datamodel are :Channel, Timesample and Layer. If these are included in the
        request, validate and initialize the class object. If these are missing get the default values from the
        dataset. The requests need to have these to be valid.

        :param request: stream: Request
        stream stream type: django.core.handlers.wsgi.WSGIRequest
        :return: None
        """
        if 'channel' in request.query_params:
            channel = request.query_params['channel']
            channelstatus = self.set_channel(channel)
        elif self.datasetobj.default_channel:
            self.channelobj = self.datasetobj.default_channel
        else:
            return BossHTTPError(404, 'No channel or default channel found', 30000)

        if 'time' in request.query_params:
            time = request.query_params['time']
            timestatus = self.set_timesample(time)
        elif self.datasetobj.default_time:
            self.timesampleobj = self.datasetobj.default_time
        else:
            return BossHTTPError(404, 'No Timesample or default timesample found', 30000)

        if 'layer' in request.query_params:
            layer = request.query_params['layer']
            layerstatus = self.set_layer(layer)
        elif self.datasetobj.default_layer:
            self.layerobj = self.datasetobj.default_layer
        else:
            return BossHTTPError(404, 'No Timesample or default timesample found', 30000)

    def initialize_optargs_meta(self, request):
        """
        Validate and initialize the optional datamodel arguments for the meta data service

        The optional arguments for the datamodel are :Channel, Timesample and Layer. If these are included in the
        request, validate and initialize the class object. If these are missing get the default values from the
        dataset.

        :param request: stream: Request stream
        stream type: django.core.handlers.wsgi.WSGIRequest
        :return: None
        """

        if 'layer' in request.query_params:
            # layer specified - check for channel and timesample
            if 'channel' in request.query_params:
                channel = request.query_params['channel']
                channelstatus = self.set_channel(channel)
            elif self.datasetobj.default_channel:
                self.channelobj = self.datasetobj.default_channel
            else:
                return BossHTTPError(404, 'No channel or default channel found', 30000)

            if 'time' in request.query_params:
                time = request.query_params['time']
                timestatus = self.set_timesample(time)
            elif self.datasetobj.default_time:
                self.timesampleobj = self.datasetobj.default_time
            else:
                return BossHTTPError(404, 'No timesample or default timesample found', 30000)

            layer = request.query_params['layer']
            layerstatus = self.set_layer(layer)

        elif 'time' in request.query_params:
            # timesample specified - check for channel 
            if 'channel' in request.query_params:
                channel = request.query_params['channel']
                channelstatus = self.set_channel(channel)
            elif self.datasetobj.default_channel:
                self.channelobj = self.datasetobj.default_channel
            else:
                return  BossHTTPError(404, 'No channel or default channel found', 30000)

            time = request.query_params['time']
            timestatus = self.set_timesample(time)

        elif 'channel' in request.query_params:
            channel = request.query_params['channel']
            channelstatus = self.set_channel(channel)

    def set_cutoutargs(self, resolution, x_range, y_range, z_range):
        """
        Validate and initialize cutout arguments from the request

        :param resolution: Integer indicating the level in the resolution hierarchy (0 = native)
        :param x_range: Python style range indicating the X coordinates  (eg. 100:200)
        :param y_range: Python style range indicating the Y coordinates (eg. 100:200)
        :param z_range: Python style range indicating the Z coordinates (eg. 100:200)
        :return: None
        """

        if resolution in range(0, self.experimentobj.num_resolution_levels):
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
                raise BossHTTPError(404, 'Incorrect cutoutargs', 30000)

        except TypeError:
            return BossHTTPError(404, 'Bad. Request. Type error in ', 30000)

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

    def set_collection(self, collection):
        """
        Set the current collection

        If a collection exists, get the django model and set the current collection
        :param collection: Collection name specified in the request
        :return: None
        """
        if Collection.objects.filter(name=str(collection)).exists():
            self.collectionobj = Collection.objects.get(name=collection)
            return True
        else:
            return BossHTTPError(404, 'Collection not found', 30000)
        return false

    def get_collection(self):
        """
        Get the collection name for the current collection
        :return: Collection name for the data model representing the current collection
        """
        if self.collectionobj:
            return self.collectionobj.name

    def set_experiment(self, experiment):
        """
        Set the current experiment

        If a experiment exists, get the django model and set the current experiment
        :param experiment: Experiment name from the request
        :return: None
        """
        if Experiment.objects.filter(name=experiment, collection=self.collectionobj).exists():
            self.experimentobj = Experiment.objects.get(name=experiment, collection=self.collectionobj)
            return True
        else:
            return BossHTTPError(404, 'Experiment not found', 30000)
            
        return false

    def get_experiment(self):
        """
        Get the experiment name for the current experiment
        :return: Experiment name for the data model representing the current experiment
        """

        if self.experimentobj:
            return self.experimentobj.name

    def set_dataset(self, dataset):
        """
        Set the current dataset

        If a dataset exists, get the django model and set the current dataset. This method also sets the current coordinate frame, default channel, default timesample and default layer if these exist for the dataset.
        :param dataset: Dataset name in the request
        :return:
        """
        if Dataset.objects.filter(name=dataset, experiment=self.experimentobj).exists():
            ds = Dataset.objects.get(name=dataset, experiment=self.experimentobj)
            self.datasetobj = ds
            if ds.coord_frame: self.coord_frame = ds.coord_frame
            if ds.default_channel: self.default_channel = ds.default_channel
            if ds.default_time: self.default_time = ds.default_time
            if ds.default_layer: self.default_layer = ds.default_layer
            return True
        else:
            return BossHTTPError(404, 'Bad Request. Dataset not found', 30000)
            
        return false

    def get_dataset(self):
        """
        Get the curent dataset
        :return: Dataset name of the current dataset
        """
        if self.datasetobj:
            return self.datasetobj.name

    def set_channel(self, channel):
        """
        Set the current channel

        If a channel exists, get the django model and set the current channel. This assumes that the dataset exists.
        :param channel: Channel name from the request
        :return:
        """
        if Channel.objects.filter(name=channel, dataset=self.datasetobj).exists():
            self.channelobj = Channel.objects.get(name=channel, dataset=self.datasetobj)
            return True
        else:
            return BossHTTPError(404, 'Bad. Request. Channel not found', 30000)

        return false

    def get_channel(self):
        """
        Get the current channel
        :return:  Channel name for the current channel
        """
        if self.channelobj:
            return self.channelobj.name

    def set_timesample(self, time):
        """
        Set the current timesample

        If a timesample exists, get the django model and set the current timesample. This assumes that the current channel exists.
        :param timesample:
        :return:
        """
        if TimeSample.objects.filter(name=time, channel=self.channelobj).exists():
            self.timesampleobj = TimeSample.objects.get(name=time, channel=self.channelobj)
            return True
        else:
            return BossHTTPError(404, 'Bad Request. Timesample not found', 30000)
            
    def get_timesample(self):
        """
        Get the current timesample
        :return: Timesample name for the current timesample
        """
        if self.timesampleobj:
            return self.timesampleobj.name

    def set_layer(self, layer):
        """
        Set the current layer

        If the layer exists, get the django model and set the current layer. This assumes that the current timesample has been set.
        :param layer: Layer name from the request
        :return:
        """
        if Layer.objects.filter(name=layer, time=self.timesampleobj).exists():
            self.layerobj = Layer.objects.get(name=layer, time=self.timesampleobj)
            return True
        else:
            return BossHTTPError(404, 'Bad. Request. Layer not found', 30000)

    def get_layer(self):
        """
        Get the current layer
        :return: Layer name of the current layer
        """
        if self.layerobj:
            return self.layerobj.name

    def set_metakey(self, metakey):
        """
        Set the metakey

        The meta key is an optional argument specified as an option argument for the metadata service
        :param metakey: Meta data key specified in the request
        :return: None
        """
        self.metakey = metakey

    def get_metakey(self):
        """
        Get the meta data key
        :return: metakey
        """
        return self.metakey

    def set_metavalue(self, metavalue):
        """
        Set the meta data value
        :param metavalue: String representing the meta data
        :return:
        """
        self.metavalue = metavalue

    def get_metavalue(self):
        """
        Get the string for the meta data value
        :return: metavalue
        """
        return self.metavalue

    def get_default_layer(self):
        """
        Get the default layer for the current dataset
        :return: Name of the default layer
        """
        return self.default_layer.name

    def get_default_channel(self):
        """
        Get the default channel for the current dataset
        :return: Name of the default channel
        """
        return self.default_channel.name

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

    def set_bosskey(self):
        """
        Create the bosskey for the request.

        The bosskey concatenates the names of the datamodel stack to create a string represting the datamodel of the request
        :return: string that represents the bosskey for the current request
        """

        self.bosskey = ""

        if self.collectionobj and self.experimentobj and self.datasetobj:
            self.bosskey = self.collectionobj.name + META_CONNECTOR + self.experimentobj.name + META_CONNECTOR + self.datasetobj.name
            self.bosskey += self.get_optkey()
            return self.bosskey
        elif self.collectionobj and self.experimentobj and self.service == 'meta':
            self.bosskey = self.collectionobj.name + META_CONNECTOR + self.experimentobj.name
            return self.bosskey
        elif self.collectionobj and self.service == 'meta':
            self.bosskey = self.collectionobj.name
            return self.bosskey
        else:
            return BossHTTPError(404, "Bad request. Did not initialize correctly", 30000)

        return self.bosskey

    def get_optkey(self):
        """
        Generate a partial bosskey for the optional datamodel objects [Channel, Experiment and Dataset]
        :return: string with the partial key
        """
        optkey = ""
        if self.layerobj:

            # Check for channel and timesample
            if self.channelobj:
                optkey = META_CONNECTOR + self.channelobj.name
            elif self.default_channel:
                optkey = META_CONNECTOR + self.default_channel.name
            else:
                return BossHTTPError(404, "Bad request. Channel and default channel not found", 30000)

            if self.timesampleobj:
                optkey += META_CONNECTOR + self.timesampleobj.name + META_CONNECTOR + self.layerobj.name
            elif self.default_time:
                optkey += META_CONNECTOR + self.default_time.name + META_CONNECTOR + self.layerobj.name
            else:
                return BossHTTPError(404, "Bad request. Timesample and default timesample not found", 30000)
  
        elif self.timesampleobj:

            # Check channel and append
            if self.channelobj:
                optkey = META_CONNECTOR + self.channelobj.name + META_CONNECTOR + self.timesampleobj.name
            elif self.default_channel:
                optkey = META_CONNECTOR + self.default_channel.name + META_CONNECTOR + self.timesampleobj.name
            else:
                return BossHTTPError(404, "Bad request. Channel and default channel not found", 30000)

        elif self.channelobj:
            optkey = META_CONNECTOR + self.channelobj.name

        return optkey

    def get_bosskey(self):
        """
        Get the bosskey for the current object
        :return: bosskey
        """
        return self.bosskey
