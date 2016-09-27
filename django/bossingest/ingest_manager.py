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

import json
import os
from io import StringIO
import io
from pkg_resources import resource_filename



import ingest
from ingest.core.validator import Validator, BossValidatorV01
from ingest.core.config import Configuration

from bossingest.serializers import IngestJobCreateSerializer
from bosscore.error import BossError, ErrorCodes, BossResourceNotFoundError

from bosscore.models import Collection, Experiment,ChannelLayer

from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndingestproj.ingestproj import IngestProj

SCHEMA_FILE_NAME = "boss-v0.1-schema.json"
class IngestManager:
    """
    Class to
    """
    config_data = None

    def __init__(self):
        """

        Args:
            config_data:
        """
        self.job_id = None
        self.config = None
        self.collection = None
        self.experiment = None
        self.channel_layer = None


    def get_schema (self):
        # Load the schema file based on the config that was provided
        schema_file = os.path.join(resource_filename("ingest", "schema"), SCHEMA_FILE_NAME)
        with open(schema_file, 'r') as file_handle:
            print ("opening")
            self.schema = json.load(file_handle)

    def validate_config_file(self,config_data):
        """
        Method to validate an ingest config file
        Args:
            ingest_config_data:

        Returns:

        """

        try:
            self.config = Configuration(config_data)
            self.validator = self.config.get_validator()
            self.validator.schema = self.config.schema
            self.validator.validate_schema()
            self.collection = self.config.config_data["database"]["collection"]
            self.experiment = self.config.config_data["database"]["experiment"]
            self.channel_layer = self.config.config_data["database"]["channel"]["name"]
        except Exception as e:
            raise BossError(" Could not validate the scheme file.{}".format(e), ErrorCodes.UNABLE_TO_VALIDATE)

        return True



    def validate_properties(self):
        """

        Returns:

        """
        # Verify Collection, Experiment and channel
        try:
            collection_obj = Collection.objects.get(name=self.collection)
            experiment_obj = Experiment.objects.get(name=self.experiment,
                                                    collection=collection_obj)
            channel_layer_obj = ChannelLayer.objects.get(name=self.channel_layer,
                                                         experiment=experiment_obj)
        except Collection.DoesNotExist:
            raise BossError("Collection {} not found".format(self.collection), ErrorCodes.RESOURCE_NOT_FOUND)
        except Experiment.DoesNotExist:
            raise BossError("Experiment {} not found".format(self.experiment), ErrorCodes.RESOURCE_NOT_FOUND)
        except ChannelLayer.DoesNotExist:
            raise BossError("Channel or Layer {} not found".format(self.channel_layer), ErrorCodes.RESOURCE_NOT_FOUND)
        # TODO If channel already exists, check corners to see if data exists.  If so question user for overwrite
        # TODO Check tile size - error if too big
        return True

    def setup_ingest(self, owner, config_data):
        """

        Args:
            ingest_config_data:

        Returns:

        """
        # Validate config data and schema
        try:
            valid_schema = self.validate_config_file(config_data)
            valid_prop = self.validate_properties()
            # TODO create channel if needed

        except BossError as err:
            raise BossError(err.message, err.error_code)


        if valid_schema is True and valid_prop is True:

            # create the django model for the job
            ingest_job_serializer_data = {
                'owner': owner,
                'collection': self.collection,
                'experiment': self.experiment,
                'channel_layer': self.channel_layer,
                'config_data': config_data,
                'x_start': self.config.config_data["ingest_job"]["extent"]["x"][0],
                'x_stop': self.config.config_data["ingest_job"]["extent"]["x"][1],
                'y_start': self.config.config_data["ingest_job"]["extent"]["y"][0],
                'y_stop': self.config.config_data["ingest_job"]["extent"]["y"][1],
                'z_start': self.config.config_data["ingest_job"]["extent"]["z"][0],
                'z_stop': self.config.config_data["ingest_job"]["extent"]["z"][1],
                't_start': self.config.config_data["ingest_job"]["extent"]["t"][0],
                't_stop': self.config.config_data["ingest_job"]["extent"]["t"][1],
                'offset_x': self.config.config_data["ingest_job"]["offset"]["x"],
                'offset_y': self.config.config_data["ingest_job"]["offset"]["y"],
                'offset_z': self.config.config_data["ingest_job"]["offset"]["z"],
                'offset_t': self.config.config_data["ingest_job"]["offset"]["t"],
                'tile_size_x': self.config.config_data["ingest_job"]["tile_size"]["x"],
                'tile_size_y': self.config.config_data["ingest_job"]["tile_size"]["y"],
                'tile_size_z': self.config.config_data["ingest_job"]["tile_size"]["z"],
                'tile_size_t': self.config.config_data["ingest_job"]["tile_size"]["t"],
            }
            serializer = IngestJobCreateSerializer(data=ingest_job_serializer_data)
            if serializer.is_valid():
                ingest_job = serializer.save()
                self.job_id = ingest_job.id

            else:
                raise BossError("{}".format(serializer.errors), ErrorCodes.SERIALIZATION_ERROR)

            #create the additional resources needed for the ingest

            return ingest_job

    def delete_ingest_job(ingest_job_id):
        """

        Args:
            ingest_job_id:

        Returns:

        """
        return ingest_job_id


