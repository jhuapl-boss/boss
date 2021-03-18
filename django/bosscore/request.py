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

import re
import numpy as np

from .models import Collection, Experiment, Channel
from .lookup import LookUpKey
from .error import BossHTTPError, BossError, ErrorCodes, BossRestArgsError
from .permissions import BossPermissionManager

META_CONNECTOR = "&"


class BossRequest:
    """
    Validator for all requests that are made to the endpoint.
    """

    def __init__(self, request, bossrequest):
        """
        Parse the request and initialize an instance of BossRequest
        Args:
            request (stream): Django Uwsgi request

        Raises:
            BossError:  If the request is invalid

        """
        self.bossrequest = bossrequest

        # Datamodel objects
        self.collection = None
        self.experiment = None
        self.channel = None

        self.default_time = None
        self.coord_frame = None

        # Endpoint service and version number from the request
        self.service = None
        self.version = None

        # Boss key representing the datamodel for a valid request
        self.base_boss_key = None

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
        self.time_request = False  # Flag indicating if the REQUEST contained a time range (True) or if auto-pop (False)

        # Request variables
        self.user = request.user
        self.method = request.method
        self.version = request.version

        # object service
        self.object_id = 0
        self.filter_ids = None

        # Validate the request based on the service
        self.service = self.bossrequest['service']

        if self.service == 'meta':
            self.validate_meta_service()

        elif self.service == 'view':
            raise BossError("Views not implemented. Specify the full request", ErrorCodes.FUTURE)

        elif self.service == 'image':
            self.validate_image_service()

        elif self.service == 'tile':
            self.validate_tile_service()

        elif self.service == 'ids':
            # Currently the validation is the same as the cutout service
            self.validate_ids_service()

        elif self.service == 'reserve':
            self.validate_reserve_service()

        elif self.service == 'boundingbox':
            self.validate_bounding_box()

        elif self.service == 'downsample':
            self.validate_downsample_service()

        else:
            self.validate_cutout_service()

    def validate_meta_service(self):
        """
        "Validate all meta data requests.

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        if 'key' in self.bossrequest:
            self.set_key(self.bossrequest['key'])
        if 'value' in self.bossrequest:
            self.set_value(self.bossrequest['value'])

    def validate_downsample_service(self):
        """
        "Validate all downsample data requests.

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

    def validate_cutout_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        # Validate filter arguments if any
        if 'ids' in self.bossrequest and self.bossrequest['ids']!= None:

            if self.channel.type != 'annotation':
                raise BossError("The channel in request has type {}. Filter is only valid for annotation channels"
                      .format(self.channel.type), ErrorCodes.DATATYPE_NOT_SUPPORTED)
            else:
                # convert ids to ints
                try:
                    self.filter_ids = np.fromstring(self.bossrequest['ids'], sep= ',', dtype=np.uint64)
                except (TypeError, ValueError)as e:
                    raise BossError("Invalid id in list of filter ids {}. {}".format(self.bossrequest['ids'], str(e)),
                                    ErrorCodes.INVALID_CUTOUT_ARGS)

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_sample
            self.time_stop = self.channel.default_time_sample + 1
            self.time_request = False
        else:
            self.set_time(time)
            self.time_request = True

        self.set_cutoutargs(int(self.bossrequest['resolution']), self.bossrequest['x_args'],
                            self.bossrequest['y_args'], self.bossrequest['z_args'])

    def validate_ids_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        # Bounding box is only valid for annotation channels
        if self.channel.type != 'annotation':
            raise BossError("The channel in request has type {}. Can only reserve IDs for annotation channels"
                            .format(self.channel.type), ErrorCodes.DATATYPE_NOT_SUPPORTED)

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_sample
            self.time_stop = self.channel.default_time_sample + 1
            self.time_request = False
        else:
            self.set_time(time)
            self.time_request = True

        self.set_cutoutargs(int(self.bossrequest['resolution']), self.bossrequest['x_args'],
                            self.bossrequest['y_args'], self.bossrequest['z_args'])

    def validate_image_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_sample
            self.time_stop = self.channel.default_time_sample + 1
        else:
            self.set_time(time)

        self.set_imageargs(self.bossrequest['orientation'], self.bossrequest['resolution'], self.bossrequest['x_args'],
                           self.bossrequest['y_args'], self.bossrequest['z_args'])

    def validate_tile_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_sample
            self.time_stop = self.channel.default_time_sample + 1
        else:
            self.set_time(time)

        self.set_tileargs(self.bossrequest['tile_size'], self.bossrequest['orientation'],
                          self.bossrequest['resolution'], self.bossrequest['x_args'], self.bossrequest['y_args'],
                          self.bossrequest['z_args'])

    def validate_reserve_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])
        if self.channel.type != 'annotation':
            raise BossError("The channel in request has type {}. Can only reserve IDs for annotation channels"
                            .format(self.channel.type),ErrorCodes.ErrorCodes.DATATYPE_NOT_SUPPORTED)

    def validate_bounding_box(self):
        """

            Args:
                webargs:

            Returns:

        """

        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        # Bounding box is only valid for annotation channels
        if self.channel.type != 'annotation':
            raise BossError("The channel in request has type {}. Can only perform bounding box operations on annotation channels"
                            .format(self.channel.type), ErrorCodes.DATATYPE_NOT_SUPPORTED)

        # TODO : validate the object id
        try:
            self.object_id = int(self.bossrequest['id'])
        except (TypeError, ValueError):
            raise BossError("The id of the object {} is not a valid int".format(self.bossrequest['id']),
                            ErrorCodes.TYPE_ERROR)

        self.validate_resolution()

    def validate_resolution(self):
        """
        Ensure requested resolution is between channel's base resolution and the base
        resolution + the experiment's number of hierarchy levels

        Raises:
            (BossError): if resolution invalid
        """
        try:
            base_res = self.channel.base_resolution
            # validate the resolution
            if int(self.bossrequest['resolution']) in range(base_res, base_res + self.experiment.num_hierarchy_levels):
                self.resolution = int(self.bossrequest['resolution'])
            else:
                raise BossError("Invalid resolution {}. The resolution has to be within {} and {}".
                                format(self.bossrequest['resolution'], base_res,
                                base_res + self.experiment.num_hierarchy_levels),
                                ErrorCodes.TYPE_ERROR)
        except (TypeError, ValueError):
            raise BossError("Type error in resolution {}".format(self.bossrequest['resolution']), ErrorCodes.TYPE_ERROR)

    def initialize_request(self, collection_name, experiment_name, channel_name):
        """
        Initialize the request

        Parse and validate all the resource names in the request

        Args:
            collection_name: Collection name from the request
            experiment_name: Experiment name from the request
            channel_name: Channel name from the request

        """
        if collection_name:
            colstatus = self.set_collection(collection_name)
            if experiment_name and colstatus:
                expstatus = self.set_experiment(experiment_name)
                if channel_name and expstatus:
                    self.set_channel(channel_name)

        self.check_permissions()
        self.set_boss_key()

    def set_cutoutargs(self, resolution, x_range, y_range, z_range):
        """
        Validate and initialize cutout arguments in the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            x_range: Python style range indicating the X coordinates  (eg. 100:200)
            y_range: Python style range indicating the Y coordinates (eg. 100:200)
            z_range: Python style range indicating the Z coordinates (eg. 100:200)

        Raises:
            BossError: For invalid requests

        """
        try:
            self.validate_resolution()

            # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

            x_coords = x_range.split(":")
            y_coords = y_range.split(":")
            z_coords = z_range.split(":")

            self.x_start = int(x_coords[0])
            self.x_stop = int(x_coords[1])

            self.y_start = int(y_coords[0])
            self.y_stop = int(y_coords[1])

            self.z_start = int(z_coords[0])
            self.z_stop = int(z_coords[1])

            # Check for valid arguments
            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop) or \
                    (self.x_start < self.coord_frame.x_start) or (self.x_stop > self.coord_frame.x_stop) or \
                    (self.y_start < self.coord_frame.y_start) or (self.y_stop > self.coord_frame.y_stop) or\
                    (self.z_start < self.coord_frame.z_start) or (self.z_stop > self.coord_frame.z_stop):
                raise BossError("Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_range, y_range, z_range),
                                ErrorCodes.INVALID_CUTOUT_ARGS)

        except (TypeError, ValueError):
            raise BossError("Type error in cutout argument{}/{}/{}/{}".format(resolution, x_range, y_range, z_range),
                            ErrorCodes.TYPE_ERROR)

    def set_imageargs(self, orientation, resolution, x_args, y_args, z_args):
        """
        Validate and initialize tile service arguments in the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            x_range: Python style range indicating the X coordinates  (eg. 100:200)
            y_range: Python style range indicating the Y coordinates (eg. 100:200)
            z_range: Python style range indicating the Z coordinates (eg. 100:200)

        Raises:
            BossError: For invalid requests

        """

        try:

            self.validate_resolution()

            # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

            if orientation == 'xy':
                x_coords = x_args.split(":")
                y_coords = y_args.split(":")
                z_coords = [int(z_args), int(z_args)+1]
                if len(x_coords) < 2 or len(y_coords) < 2:
                    raise BossError("Incorrect cutout arguments {}/{}/{}".format(x_args, y_args, z_args),
                                ErrorCodes.INVALID_CUTOUT_ARGS)

            elif orientation == 'xz':
                x_coords = x_args.split(":")
                y_coords = [int(y_args), int(y_args) + 1]
                z_coords = z_args.split(":")
                if len(x_coords) < 2 or len(z_coords) < 2:
                    raise BossError("Incorrect cutout arguments {}/{}/{}".format(x_args, y_args, z_args),
                                ErrorCodes.INVALID_CUTOUT_ARGS)

            elif orientation == 'yz':
                x_coords = [int(x_args), int(x_args) + 1]
                y_coords = y_args.split(":")
                z_coords = z_args.split(":")
                if len(y_coords) < 2 or len(z_coords) < 2:
                    raise BossError("Incorrect cutout arguments {}/{}/{}".format(x_args, y_args, z_args),
                                ErrorCodes.INVALID_CUTOUT_ARGS)
            else:
                raise BossError("Incorrect orientation {}".format(orientation), ErrorCodes.INVALID_URL)

            self.x_start = int(x_coords[0])
            self.x_stop = int(x_coords[1])

            self.y_start = int(y_coords[0])
            self.y_stop = int(y_coords[1])

            self.z_start = int(z_coords[0])
            self.z_stop = int(z_coords[1])

            # Check for valid arguments
            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop) or \
                    (self.x_start < self.coord_frame.x_start) or (self.x_stop > self.coord_frame.x_stop) or \
                    (self.y_start < self.coord_frame.y_start) or (self.y_stop > self.coord_frame.y_stop) or \
                    (self.z_start < self.coord_frame.z_start) or (self.z_stop > self.coord_frame.z_stop):
                raise BossError("Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_args, y_args, z_args),
                                ErrorCodes.INVALID_CUTOUT_ARGS)
        except (TypeError, ValueError):
            raise BossError("Type error in cutout argument{}/{}/{}/{}".format(resolution, x_args, y_args, z_args),
                            ErrorCodes.TYPE_ERROR)

    def set_tileargs(self, tile_size, orientation, resolution, x_idx, y_idx, z_idx):
        """
        Validate and initialize tile service arguments in the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            orientation:
            x_idx: X tile index
            y_idx: Y tile index
            z_idx: Z tile index

        Raises:
            BossError: For invalid requests

        """
        try:
            tile_size = int(tile_size)
            x_idx = int(x_idx)
            y_idx = int(y_idx)
            z_idx = int(z_idx)

            self.validate_resolution()

            # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

            # Get the params to pull data out of the cache
            if orientation == 'xy':
                corner = (tile_size * x_idx, tile_size * y_idx, z_idx)
                extent = (tile_size, tile_size, 1)
            elif orientation == 'yz':
                corner = (x_idx, tile_size * y_idx, tile_size * z_idx)
                extent = (1, tile_size, tile_size)
            elif orientation == 'xz':
                corner = (tile_size * x_idx, y_idx, tile_size * z_idx)
                extent = (tile_size, 1, tile_size)
            else:
                raise BossHTTPError("Invalid orientation: {}".format(orientation), ErrorCodes.INVALID_CUTOUT_ARGS)

            self.x_start = int(corner[0])
            self.x_stop = int(corner[0] + extent[0])

            self.y_start = int(corner[1])
            self.y_stop = int(corner[1] + extent[1])

            self.z_start = int(corner[2])
            self.z_stop = int(corner[2] + extent[2])

            # Check for valid arguments
            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop) or \
                    (self.x_start < self.coord_frame.x_start) or (self.x_stop > self.coord_frame.x_stop) or \
                    (self.y_start < self.coord_frame.y_start) or (self.y_stop > self.coord_frame.y_stop) or \
                    (self.z_start < self.coord_frame.z_start) or (self.z_stop > self.coord_frame.z_stop):
                raise BossError("Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_idx, y_idx, z_idx),
                                ErrorCodes.INVALID_CUTOUT_ARGS)
        except (TypeError, ValueError):
            raise BossError("Type error in cutout argument{}/{}/{}/{}".format(resolution, x_idx, y_idx, z_idx),
                            ErrorCodes.TYPE_ERROR)

    def initialize_view_request(self, webargs):
        """
        Validate and initialize views
        Args:
            webargs:
        """
        print(webargs)

    def set_service(self, service):
        """
        Set the service variable. The service can be 'meta', 'view' or 'cutout'
        Args:
            service: Service requested in the request

        Returns: None

        """
        self.service = service

    def set_collection(self, collection_name):
        """
        Validate the collection and set collection object for a valid collection.
        Args:
            collection_name: Collection name from the request

        Returns:
            Bool : True

        Raises : BossError is the collection is not found.

        """
        if Collection.objects.filter(name=str(collection_name)).exists():
            self.collection = Collection.objects.get(name=collection_name)
            if self.collection.to_be_deleted is not None:
                raise BossError("Invalid Request. This resource {} has been marked for deletion"
                                .format(collection_name),ErrorCodes.RESOURCE_MARKED_FOR_DELETION)

            return True
        else:
            raise BossError("Collection {} not found".format(collection_name), ErrorCodes.RESOURCE_NOT_FOUND)

    def get_collection(self):
        """
        Get the collection name for the current collection

        Returns:
            collection_name : Name of the collection

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
            if self.experiment.to_be_deleted is not None:
                raise BossError("Invalid Request. This resource {} has been marked for deletion"
                                .format(experiment_name),ErrorCodes.RESOURCE_MARKED_FOR_DELETION)
            self.coord_frame = self.experiment.coord_frame
        else:
            raise BossError("Experiment {} not found".format(experiment_name), ErrorCodes.RESOURCE_NOT_FOUND)

        return True

    def get_experiment(self):
        """
        Return the experiment name for the current experiment

        Returns:
            self.experiment.name (str): Experiment name for the data model representing the current experiment

        """
        if self.experiment:
            return self.experiment.name

    def set_channel(self, channel_name):
        """
        Validate and set the channel
        Args:
            channel_name: Channel name specified in the request

        Returns:

        """
        if Channel.objects.filter(name=channel_name, experiment=self.experiment).exists():
            self.channel = Channel.objects.get(name=channel_name, experiment=self.experiment)
            if self.channel.to_be_deleted is not None:
                raise BossError("Invalid Request. This resource {} has been marked for deletion"
                                .format(channel_name),ErrorCodes.RESOURCE_MARKED_FOR_DELETION)
            return True
        else:
            raise BossError("Channel {} not found".format(channel_name), ErrorCodes.RESOURCE_NOT_FOUND)

    def get_channel(self):
        """
        Return the channel name for the channel

        Returns:
            self.channel.name (str) : Name of channel

        """
        if self.channel:
            return self.channel.name

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
        Return the default timesample for the channel
        Returns:
            self.default_time (int) : Default timestep for the channel

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

    def get_filter_ids(self):
        """
        Return the liust of ids to filter the cutout on
        Returns:
            List (ints)
        """
        return self.filter_ids

    def set_boss_key(self):
        """ Set the base boss key for the request

        The boss key concatenates the names of the datamodel stack to create a string represting the request.
        Returns:
            self.bosskey(str) : String that represents the boss key for the current request
        """
        if self.collection and self.experiment and self.channel:
            self.base_boss_key = self.collection.name + META_CONNECTOR + self.experiment.name + META_CONNECTOR \
                                 + self.channel.name
        elif self.collection and self.experiment and self.service == 'meta':
            self.base_boss_key = self.collection.name + META_CONNECTOR + self.experiment.name
        elif self.collection and self.service == 'meta':
            self.base_boss_key = self.collection.name
        else:
            raise BossError("Error creating the boss key", ErrorCodes.UNABLE_TO_VALIDATE)

    def check_permissions(self):
        """ Set the base boss key for the request

        The boss key concatenates the names of the datamodel stack to create a string represting the request.
        Returns:
            self.bosskey(str) : String that represents the boss key for the current request
        """
        if self.service == 'cutout' or self.service == 'image' or self.service == 'tile'\
                or self.service == 'boundingbox' or self.service == 'downsample':
            # TODO SH Hack added to allow us to quickly make channels public without logging in.
            # These are bossdb IDs.
            if self.channel.id in [325, 326, 331, 333, 334, 338, 339, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382,
                                   383, 386, 390, 392, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415,
                                   416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432,
                                   433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449,
                                   450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466,
                                   467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483,
                                   484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500,
                                   501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517,
                                   518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534,
                                   535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551,
                                   552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568,
                                   569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585,
                                   586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602,
                                   603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619,
                                   620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636,
                                   637, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 650, 651, 652, 653,
                                   654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670,
                                   671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687,
                                   688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704,
                                   705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721,
                                   722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738,
                                   739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 753, 754, 755,
                                   756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772,
                                   773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789,
                                   790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806,
                                   807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823,
                                   824, 825, 826, 827, 828, 829, 830, 831, 832, 833, 834, 835, 836, 837, 838, 839, 840,
                                   841, 842, 843, 844, 845, 846, 847, 848, 849, 850, 851, 852, 853, 854, 855, 856, 857,
                                   858, 859, 860, 861, 862, 863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874,
                                   875, 876, 877, 878, 879, 880, 881, 882, 883, 884, 885, 886, 887, 888, 889, 890, 891,
                                   892, 893, 894, 895, 896, 897, 898, 899, 900, 901, 902, 903, 904, 905, 906, 907, 908,
                                   909, 910, 911, 912, 913, 914, 915, 916, 917, 918, 919, 920, 921, 922, 923, 924, 925,
                                   926, 927, 928, 929, 930, 931, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942,
                                   943, 944, 945, 946, 947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959,
                                   962, 963, 964, 965, 966, 967, 975, 976, 977, 978, 979, 980, 981, 982, 983, 984, 985,
                                   986, 987, 988, 989, 993, 995, 997, 1004, 1033, 1034, 1035, 1037, 1039, 1040, 1041,
                                   1042, 1043, 1044, 1045, 1046, 1047, 1062, 1066, 1067, 1068, 1069, 1070, 1071, 1072,
                                   1073, 1074, 1080, 1083, 1090, 1091, 1092, 1093, 1094, 1095, 1096, 1097, 1098, 1099,
                                   1100, 1101, 1102, 1103, 1105, 1106, 1107, 1108, 1109, 1110]:
                return
            perm = BossPermissionManager.check_data_permissions(self.user, self.channel, self.method)
        elif self.service == 'ids':
            perm = BossPermissionManager.check_data_permissions(self.user, self.channel, self.method)
        elif self.service == 'meta':
            if self.collection and self.experiment and self.channel:
                obj = self.channel
            elif self.collection and self.experiment:
                obj = self.experiment
            elif self.collection:
                obj = self.collection
            else:
                raise BossError("Error encountered while checking permissions for this request",
                                ErrorCodes.UNABLE_TO_VALIDATE)
            perm = BossPermissionManager.check_resource_permissions(self.user, obj, self.method)
        elif self.service == 'reserve':
            perm = BossPermissionManager.check_object_permissions(self.user, self.channel, self.method)

        if not perm:
            raise BossError("This user does not have the required permissions", ErrorCodes.MISSING_PERMISSION)

    def get_boss_key(self):
        """
        Get the boss key for the current object

        The boss key is the compound identifier using the "name" attribute of the data model resources used
        in the request

        Returns:
            self.boss_key (str) : The base boss key for the request
        """
        return self.base_boss_key

    def get_lookup_key(self):
        """
        Returns the base lookup key for the request, excluding the resolution and time sample

        The lookup key is the compound identifier using the "id" attribute of the data model resources used
        in the request

        Returns:
            lookup (str) : The base lookup key that correspond to the request

        """
        return LookUpKey.get_lookup_key(self.base_boss_key).lookup_key

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
                if self.time_start > self.experiment.num_time_samples:
                    raise BossError("Invalid time range {}. Start time is greater than the maximum time sample {}"
                                         .format(time, str(self.experiment.num_time_samples)), ErrorCodes.INVALID_URL)
            else:
                raise BossError("Unable to parse time sample argument {}".format(time), ErrorCodes.INVALID_URL)
            if tstop:
                self.time_stop = int(tstop)
                if self.time_start > self.time_stop or self.time_stop > self.experiment.num_time_samples + 1:
                    raise BossError("Invalid time range {}. End time is greater than the start time or out of "
                                         "bounds with maximum time sample {}".format
                                         (time, str(self.experiment.num_time_samples)), ErrorCodes.INVALID_URL)
            else:
                self.time_stop = self.time_start + 1

    def get_time(self):
        """
        Return the time step range
        Returns:
            Time sample range

        """
        return range(self.time_start, self.time_stop)
