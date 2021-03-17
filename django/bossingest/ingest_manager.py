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
import jsonschema
import boto3
import math
from django.utils import timezone

from ingestclient.core.config import Configuration
from ingestclient.core.backend import BossBackend

from bossingest.serializers import IngestJobCreateSerializer
from bossingest.models import IngestJob
from bossingest.utils import get_sqs_num_msgs

from bosscore.error import BossError, ErrorCodes
from bosscore.models import Collection, Experiment, Channel
from bosscore.lookup import LookUpKey

from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndqueue.ingestqueue import IngestQueue
from ndingest.ndqueue.tileindexqueue import TileIndexQueue
from ndingest.ndqueue.tileerrorqueue import TileErrorQueue
from ndingest.ndingestproj.bossingestproj import BossIngestProj
from ndingest.nddynamo.boss_tileindexdb import BossTileIndexDB
from ndingest.ndbucket.tilebucket import TileBucket
from ndingest.util.bossutil import BossUtil

import bossutils
from bossutils.ingestcreds import IngestCredentials

# Get the ingest bucket name from boss.config
config = bossutils.configuration.BossConfig()
INGEST_BUCKET = config["aws"]["ingest_bucket"]
INGEST_LAMBDA = config["lambda"]["ingest_function"]
TILE_UPLOADED_LAMBDA = config["lambda"]["tile_uploaded_function"]
TILE_INDEX = config["aws"]["tile-index-table"]
ENDPOINT_DB = config["aws"]["db"]


CONNECTOR = '&'
MAX_NUM_MSG_PER_FILE = 10000
MAX_SQS_BATCH_SIZE = 10

WAIT_FOR_QUEUES_SECS = 180

UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG = "Upload queue is not empty"
INGEST_QUEUE_NOT_EMPTY_ERR_MSG = "Ingest queue is not empty"
TILE_INDEX_QUEUE_NOT_EMPTY_ERR_MSG = "Tile ingest queue is not empty"
TILE_ERROR_QUEUE_NOT_EMPTY_ERR_MSG = "Tile error queue is not empty"
NOT_IN_UPLOADING_STATE_ERR_MSG = 'Ingest job must be in UPLOADING state moving to WAIT_ON_QUEUES state'
NOT_IN_WAIT_ON_QUEUES_STATE_ERR_MSG = 'Ingest job must be in WAIT_ON_QUEUES state moving to Completing state'
ALREADY_COMPLETING_ERR_MSG = "Ingest job already completing"

class IngestManager:
    """
    Helper class for the boss ingest service

    """

    def __init__(self):
        """
         Init function
        """
        self.job = None
        self.owner = None
        self.config = None
        self.validator = None
        self.collection = None
        self.experiment = None
        self.channel = None
        self.resolution = 0
        self.nd_proj = None

        # Some stats for testing
        self.file_index = 0
        self.num_of_chunks = 0
        self.count_of_tiles = 0

    def validate_config_file(self, config_data):
        """
        Method to validate an ingest config file. This uses the Ingest client for validation.

        Args:
            config_data:

        Returns:
            (bool) : Status of the validation

        Raises:
            BossError : For exceptions that happen during validation

        """

        try:
            # Validate the schema
            self.config = Configuration(config_data)
            self.validator = self.config.get_validator()
            self.validator.schema = self.config.schema
            results = self.validator.validate()
        except jsonschema.ValidationError as e:
            raise BossError("Schema validation failed! {}".format(e), ErrorCodes.UNABLE_TO_VALIDATE)
        except Exception as e:
            raise BossError("Could not validate the schema file.{}".format(e), ErrorCodes.UNABLE_TO_VALIDATE)

        if len(results['error']) > 0:
            raise BossError('Could not validate the schema: ' + '\n'.join(results['error']),
                ErrorCodes.UNABLE_TO_VALIDATE)

        return True

    def validate_properties(self):
        """
        Validate the  Collection, experiment and  channel being used for the ingest job

        Returns:
            (bool) : Status of the validation

        Raises:
            BossError : If the collection, experiment or channel are not valid


        """
        # Verify Collection, Experiment and channel
        try:
            self.collection = Collection.objects.get(name=self.config.config_data["database"]["collection"])
            self.experiment = Experiment.objects.get(name=self.config.config_data["database"]["experiment"],
                                                     collection=self.collection)
            self.channel = Channel.objects.get(name=self.config.config_data["database"]["channel"],
                                               experiment=self.experiment)
            self.resolution = self.channel.base_resolution

        except Collection.DoesNotExist:
            raise BossError("Collection {} not found".format(self.collection), ErrorCodes.RESOURCE_NOT_FOUND)
        except Experiment.DoesNotExist:
            raise BossError("Experiment {} not found".format(self.experiment), ErrorCodes.RESOURCE_NOT_FOUND)
        except Channel.DoesNotExist:
            raise BossError("Channel {} not found".format(self.channel), ErrorCodes.RESOURCE_NOT_FOUND)

        # TODO If channel already exists, check corners to see if data exists.  If so question user for overwrite
        # TODO Check tile size - error if too big
        return True

    def setup_ingest(self, creator, config_data):
        """
        Setup the ingest job. This is the primary method for the ingest manager.
        It creates the ingest job and queues required for the ingest. It also uploads the messages for the ingest

        Args:
            creator: The validated user from the request to create the ingest jon
            config_data : Config data to create the ingest job

        Returns:
            IngestJob : data model containing the ingest job

        Raises:
            BossError : For all exceptions that happen

        """
        # Validate config data and schema

        self.owner = creator
        try:
            valid_schema = self.validate_config_file(config_data)
            valid_prop = self.validate_properties()
            if valid_schema is True and valid_prop is True:
                # create the django model for the job
                self.job = self.create_ingest_job()

                # create the additional resources needed for the ingest
                # initialize the ndingest project for use with the library
                proj_class = BossIngestProj.load()
                self.nd_proj = proj_class(self.collection.name, self.experiment.name, self.channel.name,
                                          self.resolution, self.job.id)

                # Create the upload queue
                upload_queue = self.create_upload_queue()
                self.job.upload_queue = upload_queue.url

                # Create the ingest queue
                if self.job.ingest_type == IngestJob.TILE_INGEST:
                    ingest_queue = self.create_ingest_queue()
                    self.job.ingest_queue = ingest_queue.url
                    tile_index_queue = self.create_tile_index_queue()
                    self.add_trigger_tile_uploaded_lambda_from_queue(tile_index_queue.arn)
                    self.create_tile_error_queue()
                elif self.job.ingest_type == IngestJob.VOLUMETRIC_INGEST:
                    # Will the management console be ok with ingest_queue being null?
                    pass

                # Call the step function to populate the queue.
                self.job.step_function_arn = self.populate_upload_queue(self.job)

                # Compute # of tiles or chunks in the job
                x_extent = self.job.x_stop - self.job.x_start
                y_extent = self.job.y_stop - self.job.y_start
                z_extent = self.job.z_stop - self.job.z_start
                t_extent = self.job.t_stop - self.job.t_start
                num_tiles_in_x = math.ceil(x_extent/self.job.tile_size_x)
                num_tiles_in_y = math.ceil(y_extent/self.job.tile_size_y)
                num_tiles_in_z = math.ceil(z_extent/self.job.tile_size_z)
                num_tiles_in_t = math.ceil(t_extent / self.job.tile_size_t)
                self.job.tile_count = num_tiles_in_x * num_tiles_in_y * num_tiles_in_z * num_tiles_in_t
                self.job.save()

        except BossError as err:
            raise BossError(err.message, err.error_code)
        except Exception as e:
            raise BossError("Unable to create the upload and ingest queue.{}".format(e),
                            ErrorCodes.BOSS_SYSTEM_ERROR)
        return self.job

    def create_ingest_job(self):
        """
        Create a new ingest job using the parameters in the ingest config data file

        Returns:
            IngestJob : Data model with the current ingest job

        Raises:
            BossError : For serialization errors that occur while creating a ingest job or if ingest_type is invalid
        """

        ingest_job_serializer_data = {
            'creator': self.owner,
            'collection': self.collection.name,
            'experiment': self.experiment.name,
            'channel': self.channel.name,
            'collection_id': self.collection.id,
            'experiment_id': self.experiment.id,
            'channel_id': self.channel.id,
            'config_data': json.dumps(self.config.config_data),
            'resolution': self.resolution,
            'x_start': self.config.config_data["ingest_job"]["extent"]["x"][0],
            'x_stop': self.config.config_data["ingest_job"]["extent"]["x"][1],
            'y_start': self.config.config_data["ingest_job"]["extent"]["y"][0],
            'y_stop': self.config.config_data["ingest_job"]["extent"]["y"][1],
            'z_start': self.config.config_data["ingest_job"]["extent"]["z"][0],
            'z_stop': self.config.config_data["ingest_job"]["extent"]["z"][1],
            't_start': self.config.config_data["ingest_job"]["extent"]["t"][0],
            't_stop': self.config.config_data["ingest_job"]["extent"]["t"][1],
        }

        if "ingest_type" in self.config.config_data["ingest_job"]:
            ingest_job_serializer_data["ingest_type"] = self._convert_string_to_ingest_job(
                self.config.config_data["ingest_job"]["ingest_type"])
        else:
            ingest_job_serializer_data["ingest_type"] = IngestJob.TILE_INGEST

        if ingest_job_serializer_data["ingest_type"] == IngestJob.TILE_INGEST:
            ingest_job_serializer_data['tile_size_x'] = self.config.config_data["ingest_job"]["tile_size"]["x"]
            ingest_job_serializer_data['tile_size_y'] = self.config.config_data["ingest_job"]["tile_size"]["y"]
            #ingest_job_serializer_data['tile_size_z'] = self.config.config_data["ingest_job"]["tile_size"]["z"]
            ingest_job_serializer_data['tile_size_z'] = 1
            ingest_job_serializer_data['tile_size_t'] = self.config.config_data["ingest_job"]["tile_size"]["t"]
        elif ingest_job_serializer_data["ingest_type"] == IngestJob.VOLUMETRIC_INGEST:
            ingest_job_serializer_data['tile_size_x'] = self.config.config_data["ingest_job"]["chunk_size"]["x"]
            ingest_job_serializer_data['tile_size_y'] = self.config.config_data["ingest_job"]["chunk_size"]["y"]
            ingest_job_serializer_data['tile_size_z'] = self.config.config_data["ingest_job"]["chunk_size"]["z"]
            ingest_job_serializer_data['tile_size_t'] = 1
        else:
            raise BossError('Invalid ingest_type: {}'.format(ingest_job_serializer_data["ingest_type"]), ErrorCodes.UNABLE_TO_VALIDATE)

        serializer = IngestJobCreateSerializer(data=ingest_job_serializer_data)
        if serializer.is_valid():
            ingest_job = serializer.save()
            return ingest_job

        else:
            raise BossError("{}".format(serializer.errors), ErrorCodes.SERIALIZATION_ERROR)

    def _convert_string_to_ingest_job(self, s):
        """
        Convert a string representation of ingest_type to int.

        Args:
            s (str):

        Returns:
            (int): IngestJob.TILE_INGEST | IngestJob.VOLUMETRIC_INGEST

        Raises:
            (BossError): If string is invalid.
        """
        lowered = s.lower()
        if lowered == 'tile':
            return IngestJob.TILE_INGEST
        if lowered == 'volumetric':
            return IngestJob.VOLUMETRIC_INGEST

        raise BossError('Unknown ingest_type: {}'.format(s))

    def get_ingest_job(self, ingest_job_id):
        """
        Get the ingest job with the specific id
        Args:
            ingest_job_id: Id of the ingest job

        Returns:
            IngestJob : Data model with the ingest job if the id is valid

        Raises:
            BossError : If the ingets job id does not exist

        """
        try:
            ingest_job = IngestJob.objects.get(id=ingest_job_id)
            return ingest_job
        except IngestJob.DoesNotExist:
            raise BossError("The ingest job with id {} does not exist".format(str(ingest_job_id)),
                            ErrorCodes.OBJECT_NOT_FOUND)

    def get_ingest_job_upload_queue(self, ingest_job):
        """
        Return the upload queue for an ingest job
        Args:
            ingest_job: Ingest job model

        Returns:
            Ndingest.uploadqueue
        """
        proj_class = BossIngestProj.load()
        self.nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                                  ingest_job.resolution, ingest_job.id)
        queue = UploadQueue(self.nd_proj, endpoint_url=None)
        return queue

    def get_ingest_job_tile_index_queue(self, ingest_job):
        """
        Return the tile index queue for an ingest job
        Args:
            ingest_job: Ingest job model

        Returns:
            ndingest.TileIndexQueue
        """
        proj_class = BossIngestProj.load()
        self.nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                                  ingest_job.resolution, ingest_job.id)
        queue = TileIndexQueue(self.nd_proj, endpoint_url=None)
        return queue

    def get_ingest_job_tile_error_queue(self, ingest_job):
        """
        Return the tile index queue for an ingest job
        Args:
            ingest_job: Ingest job model

        Returns:
            ndingest.TileIndexQueue
        """
        proj_class = BossIngestProj.load()
        self.nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                                  ingest_job.resolution, ingest_job.id)
        queue = TileErrorQueue(self.nd_proj, endpoint_url=None)
        return queue

    def get_ingest_job_ingest_queue(self, ingest_job):
        """
        Return the ingest queue for an ingest job

        Args:
            ingest_job: Ingest job model

        Returns:
            Ndingest.ingestqueue
        """
        proj_class = BossIngestProj.load()
        self.nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                                  ingest_job.resolution, ingest_job.id)
        queue = IngestQueue(self.nd_proj, endpoint_url=None)
        return queue

    def calculate_remaining_queue_wait(self, ingest_job):
        """
        Return how many seconds remain while waiting for queues to clear.
        
        Once the wait period elapses, it might be safe to transition from
        WAIT_ON_QUEUES to the COMPLETING state.

        Args:
            ingest_job: Ingest job model

        Returns:
            (int): Seconds.
        """
        if ingest_job.wait_on_queues_ts is None:
            return WAIT_FOR_QUEUES_SECS

        elapsed_secs = timezone.now() - ingest_job.wait_on_queues_ts
        secs_remaining = WAIT_FOR_QUEUES_SECS - elapsed_secs.total_seconds()
        if secs_remaining < 0:
            return 0
        return secs_remaining

    def try_enter_wait_on_queue_state(self, ingest_job):
        """
        Try to move the ingest job to the WAIT_ON_QUEUES state.

        Args:
            ingest_job: Ingest job model

        Returns:
            (dict): { status: (job status str), wait_secs: (int) - # seconds client should wait }

        Raises:
            (BossError): If job not in UPLOADING state.
        """
        if ingest_job.status == IngestJob.WAIT_ON_QUEUES:
            return {
                'job_status': IngestJob.WAIT_ON_QUEUES,
                'wait_secs': self.calculate_remaining_queue_wait(ingest_job)
            }
        elif ingest_job.status != IngestJob.UPLOADING:
            raise BossError(NOT_IN_UPLOADING_STATE_ERR_MSG, ErrorCodes.BAD_REQUEST)

        self.ensure_queues_empty(ingest_job)

        rows_updated = (IngestJob.objects
            .filter(id=ingest_job.id, status=IngestJob.UPLOADING)
            .update(status=IngestJob.WAIT_ON_QUEUES, wait_on_queues_ts=timezone.now())
            )
        
        # No update occurred, check if job status already WAIT_ON_QUEUES.
        if rows_updated == 0:
            refresh_job = self.get_ingest_job(ingest_job.id)
            if refresh_job.status != IngestJob.WAIT_ON_QUEUES:
                raise BossError(NOT_IN_UPLOADING_STATE_ERR_MSG, ErrorCodes.BAD_REQUEST)

        return {
            'job_status': IngestJob.WAIT_ON_QUEUES,
            'wait_secs': self.calculate_remaining_queue_wait(ingest_job)
        }

    def try_start_completing(self, ingest_job):
        """
        Tries to start completion process.

        It is assumed that the ingest job status is currently WAIT_ON_QUEUES.

        If ingest_job status can be set to COMPLETING, then this process "wins"
        and starts the completion process.

        Args:
            ingest_job: Ingest job model

        Returns:
            (dict): { status: (job status str), wait_secs: (int) - # seconds client should wait }

        Raises:
            (BossError): If completion process cannot be started or is already
            in process.
        """
        completing_success = {
            'job_status': IngestJob.COMPLETING,
            'wait_secs': 0
        }

        if ingest_job.status == IngestJob.COMPLETING:
            return completing_success

        try:
            self.ensure_queues_empty(ingest_job)
        except BossError as be:
            # Ensure state goes back to UPLOADING if the upload queue isn't
            # empty.
            if be.message == UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG:
                ingest_job.status = IngestJob.UPLOADING
                ingest_job.save()
            raise

        if ingest_job.status != IngestJob.WAIT_ON_QUEUES:
            raise BossError(NOT_IN_WAIT_ON_QUEUES_STATE_ERR_MSG, ErrorCodes.BAD_REQUEST)

        wait_remaining = self.calculate_remaining_queue_wait(ingest_job)
        if wait_remaining > 0:
            return {
                'job_status': IngestJob.WAIT_ON_QUEUES,
                'wait_secs': wait_remaining
            }

        rows_updated = (IngestJob.objects
            .exclude(status=IngestJob.COMPLETING)
            .filter(id=ingest_job.id)
            .update(status=IngestJob.COMPLETING)
            )
        
        # If successfully set status to COMPLETING, kick off the completion
        # process.  Otherwise, completion already started.
        if rows_updated > 0:
            self._start_completion_activity(ingest_job)

        return completing_success

    def _start_completion_activity(self, ingest_job):
        """
        Start the step function activity that checks a tile ingest job for
        missing tiles.

        This method SHOULD NOT be called by anyone but this class.  We do not
        any more than 1 completion activity running for an ingest job.
        
        Args:
            ingest_job: Ingest job model

        Returns:
            (str|None): Arn of step function if successful

        Raises:
        """
        if ingest_job.ingest_type != IngestJob.TILE_INGEST:
            return None
        args = {
            'tile_index_table': config['aws']['tile-index-table'],
            'status': 'complete',
            'region': bossutils.aws.get_region(),
            'db_host': ENDPOINT_DB,
            'job': {
                'collection': ingest_job.collection_id,
                'experiment': ingest_job.experiment_id,
                'channel': ingest_job.channel_id,
                'task_id': ingest_job.id,
                'resolution': ingest_job.resolution,
                'z_chunk_size': 16, # Number of z slices in a cuboid. 
                'upload_queue': ingest_job.upload_queue,
                'ingest_queue': ingest_job.ingest_queue,
                'ingest_type': ingest_job.ingest_type
            }
        }

        session = bossutils.aws.get_session()
        scan_sfn = config['sfn']['complete_ingest_sfn']
        return bossutils.aws.sfn_execute(session, scan_sfn, args)

    def ensure_queues_empty(self, ingest_job):
        """
        As part of verifying that an ingest job is ready to complete, check
        each SQS queue associated with the ingest job.

        Args:
            ingest_job: Ingest job model

        Raises:
            (BossError): If a queue is not empty.
        """
        upload_queue = self.get_ingest_job_upload_queue(ingest_job)
        if get_sqs_num_msgs(upload_queue.url, upload_queue.region_name) > 0:
            raise BossError(UPLOAD_QUEUE_NOT_EMPTY_ERR_MSG, ErrorCodes.BAD_REQUEST)

        ingest_queue = self.get_ingest_job_ingest_queue(ingest_job)
        if get_sqs_num_msgs(ingest_queue.url, ingest_queue.region_name) > 0:
            raise BossError(INGEST_QUEUE_NOT_EMPTY_ERR_MSG, ErrorCodes.BAD_REQUEST)

        tile_index_queue = self.get_ingest_job_tile_index_queue(ingest_job)
        if get_sqs_num_msgs(tile_index_queue.url, tile_index_queue.region_name) > 0:
            raise BossError(TILE_INDEX_QUEUE_NOT_EMPTY_ERR_MSG, ErrorCodes.BAD_REQUEST)

        tile_error_queue = self.get_ingest_job_tile_error_queue(ingest_job)
        if get_sqs_num_msgs(tile_error_queue.url, tile_error_queue.region_name) > 0:
            raise BossError(TILE_ERROR_QUEUE_NOT_EMPTY_ERR_MSG, ErrorCodes.BAD_REQUEST)

    def cleanup_ingest_job(self, ingest_job, job_status):
        """
        Delete or complete an ingest job with a specific id. Note this deletes the queues, credentials and all the remaining tiles
        in the tile bucket for this job id. It does not delete the ingest job datamodel but changes its state.
        Args:
            ingest_job: Ingest job to cleanup
            job_status(int): Status to update to

        Returns:
            (int): ingest job id for the job that was successfully deleted

        Raises:
            BossError : If the the job id is not valid or any exception happens in deletion process

        """
        try:
            # cleanup ingest job
            proj_class = BossIngestProj.load()
            self.nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                                      ingest_job.resolution, ingest_job.id)

            # delete the queues
            self.delete_upload_queue()
            if ingest_job.ingest_type != IngestJob.VOLUMETRIC_INGEST:
                self.delete_ingest_queue()
                self.delete_tile_index_queue()
                self.delete_tile_error_queue()

            ingest_job.status = job_status
            ingest_job.ingest_queue = None
            ingest_job.upload_queue = None
            ingest_job.end_date = timezone.now()
            ingest_job.save()

            # Remove ingest credentials for a job
            self.remove_ingest_credentials(ingest_job.id)

        except Exception as e:
            raise BossError("Unable to complete cleanup {}".format(e), ErrorCodes.BOSS_SYSTEM_ERROR)
        except IngestJob.DoesNotExist:
            raise BossError("Ingest job with id {} does not exist".format(ingest_job.id), ErrorCodes.OBJECT_NOT_FOUND)
        return ingest_job.id

    def create_upload_queue(self):
        """
        Create an upload queue for an ingest job using the ndingest library
        Returns:
            UploadQueue : Returns a upload queue object

        """
        UploadQueue.createQueue(self.nd_proj, endpoint_url=None)
        queue = UploadQueue(self.nd_proj, endpoint_url=None)
        return queue

    def create_tile_index_queue(self):
        """
        Create an tile index queue for an ingest job using the ndingest library
        Returns:
            TileIndexQueue : Returns a tile index queue object

        """
        TileIndexQueue.createQueue(self.nd_proj, endpoint_url=None)
        queue = TileIndexQueue(self.nd_proj, endpoint_url=None)
        return queue

    def create_tile_error_queue(self):
        """
        Create an tile error queue for an ingest job using the ndingest library
        Returns:
            TileErrorQueue : Returns a tile index queue object

        """
        TileErrorQueue.createQueue(self.nd_proj, endpoint_url=None)
        queue = TileErrorQueue(self.nd_proj, endpoint_url=None)
        return queue

    def create_ingest_queue(self):
        """
        Create an ingest queue for an ingest job using the ndingest library
        Returns:
            IngestQueue : Returns a ingest queue object

        """
        IngestQueue.createQueue(self.nd_proj, endpoint_url=None)
        queue = IngestQueue(self.nd_proj, endpoint_url=None)
        return queue

    def delete_upload_queue(self):
        """
        Delete the current upload queue
        Returns:
            None

        """
        UploadQueue.deleteQueue(self.nd_proj, endpoint_url=None)

    def delete_tile_index_queue(self):
        """
        Delete the current tile index queue.  Also removes the queue as an
        event trigger for the tile uploaded lambda.

        Returns:
            None

        """
        # self.remove_trigger_tile_uploaded_lambda_from_queue(queue.arn)
        TileIndexQueue.deleteQueue(self.nd_proj, endpoint_url=None, delete_deadletter_queue=True)

    def delete_tile_error_queue(self):
        """
        Delete the current tile error queue
        Returns:
            None

        """
        TileErrorQueue.deleteQueue(self.nd_proj, endpoint_url=None)

    def delete_ingest_queue(self):
        """
        Delete the current ingest queue
        Returns:
            None

        """
        IngestQueue.deleteQueue(self.nd_proj, endpoint_url=None)

    def add_trigger_tile_uploaded_lambda_from_queue(self, queue_arn, num_msgs=1):
        """
        Adds an SQS event trigger to the tile uploaded lambda.

        Args:
            queue_arn (str): Arn of SQS queue that will be the trigger source.
            num_msgs (optional[int]): Number of messages to send to the lambda.  Defaults to 1, max 10.

        Raises:
            (ValueError): if num_msgs is greater than the SQS max batch size.
        """
        if num_msgs < 1 or num_msgs > MAX_SQS_BATCH_SIZE:
            raise ValueError('trigger_tile_uploaded_lambda_from_queue(): Bad num_msgs: {}'.format(num_msgs))

        client = boto3.client('lambda', region_name=bossutils.aws.get_region())
        client.create_event_source_mapping(
            EventSourceArn=queue_arn,
            FunctionName=TILE_UPLOADED_LAMBDA,
            BatchSize=num_msgs)

    def remove_trigger_tile_uploaded_lambda_from_queue(self, queue_arn):
        """
        Removes an SQS event triggger from the tile uploaded lambda.

        Args:
            queue_arn (str): Arn of SQS queue that will be the trigger source.
        """
        client = boto3.client('lambda', region_name=bossutils.aws.get_region())
        resp = client.list_event_source_mappings(
            EventSourceArn=queue_arn,
            FunctionName=TILE_UPLOADED_LAMBDA)
        for evt in resp['EventSourceMappings']:
            client.delete_event_source_mapping(UUID=evt['UUID'])

    def get_tile_bucket(self):
        """
        Get the name of the ingest tile bucket

        Returns:
            Str: Name of the Tile bucket

        """
        return TileBucket.getBucketName()

    def populate_upload_queue(self, job):
        """Execute the populate_upload_queue Step Function

        Args:
            job (IngestJob):

        Returns:
            (string): ARN of the StepFunction Execution started

        Raises:
            (BossError) : if there is no valid ingest job
        """
        args = self._generate_upload_queue_args(job)
        if job.ingest_type == IngestJob.TILE_INGEST:
            args['upload_sfn'] = config['sfn']['upload_sfn']
        elif job.ingest_type == IngestJob.VOLUMETRIC_INGEST:
            args['upload_sfn'] = config['sfn']['volumetric_upload_sfn']
        else:
            raise BossError(
                "Ingest job's ingest_type has invalid value: {}".format(
                    job.ingest_type), ErrorCodes.UNABLE_TO_VALIDATE)

        session = bossutils.aws.get_session()
        populate_sfn = config['sfn']['populate_upload_queue']
        arn = bossutils.aws.sfn_execute(session, populate_sfn, args)

        return arn

    def _generate_upload_queue_args(self, ingest_job):
        """
        Generate dictionary to include in messages placed in the tile upload queue.
        
        Args:
            ingest_job (IngestJob):

        Returns:
            (dict)

        Raises:
            (BossError): If ingest_job.ingest_type invalid.
        """

        bosskey = ingest_job.collection + CONNECTOR + ingest_job.experiment + CONNECTOR + ingest_job.channel
        lookup_key = (LookUpKey.get_lookup_key(bosskey)).lookup_key
        [col_id, exp_id, ch_id] = lookup_key.split('&')

        args = {
            'job_id': ingest_job.id,
            'upload_queue': ingest_job.upload_queue,
            'ingest_queue': ingest_job.ingest_queue,

            'resolution': ingest_job.resolution,
            'project_info': lookup_key.split(CONNECTOR),
            'ingest_type': ingest_job.ingest_type,

            't_start': ingest_job.t_start,
            't_stop': ingest_job.t_stop,
            't_tile_size': 1,

            'x_start': ingest_job.x_start,
            'x_stop': ingest_job.x_stop,
            'x_tile_size': ingest_job.tile_size_x,

            'y_start': ingest_job.y_start,
            'y_stop': ingest_job.y_stop,
            'y_tile_size': ingest_job.tile_size_y,

            'z_start': ingest_job.z_start,
            'z_stop': ingest_job.z_stop,
            'z_tile_size': 1
        }


        if ingest_job.ingest_type == IngestJob.TILE_INGEST:
            # Always the Boss cuboid z size for tile jobs.
            args['z_chunk_size'] = 16
        elif ingest_job.ingest_type == IngestJob.VOLUMETRIC_INGEST:
            # tile_size_* holds the chunk size dimensions for volumetric jobs.
            args['z_chunk_size'] = ingest_job.tile_size_z
        else:
            raise BossError(
                "Ingest job's ingest_type has invalid value: {}".format(
                    self.job.ingest_type), ErrorCodes.UNABLE_TO_VALIDATE)
        return args

    def invoke_ingest_lambda(self, ingest_job, num_invokes=1):
        """Method to trigger extra lambda functions to make sure all the ingest jobs that are actually fully populated
        kick through

        Args:
            ingest_job: Ingest job object
            num_invokes(int): number of invocations to fire

        Returns:

        """
        bosskey = ingest_job.collection + CONNECTOR + ingest_job.experiment + CONNECTOR + ingest_job.channel
        lookup_key = (LookUpKey.get_lookup_key(bosskey)).lookup_key
        [col_id, exp_id, ch_id] = lookup_key.split('&')
        project_info = [col_id, exp_id, ch_id]
        fake_chunk_key = (BossBackend(self.config)).encode_chunk_key(16, project_info,
                                                                     ingest_job.resolution,
                                                                     0, 0, 0, 0)

        event = {"ingest_job": ingest_job.id,
                 "chunk_key": fake_chunk_key,
                 "function-name": INGEST_LAMBDA,
                 "lambda-name": "ingest"}

        # Invoke Ingest lambda functions
        lambda_client = boto3.client('lambda', region_name=bossutils.aws.get_region())
        for _ in range(0, num_invokes):
            lambda_client.invoke(FunctionName=INGEST_LAMBDA,
                                 InvocationType='Event',
                                 Payload=json.dumps(event).encode())

    def generate_ingest_credentials(self, ingest_job):
        """
        Create new ingest credentials for a job
        Args:
            ingest_job: Ingest job model
        Returns:
            None
        Raises:
            (ValueError): On bad ingest_type

        """
        # Generate credentials for the ingest_job
        upload_queue = self.get_ingest_job_upload_queue(ingest_job)
        tile_index_queue = None
        ingest_creds = IngestCredentials()
        if ingest_job.ingest_type == IngestJob.TILE_INGEST:
            bucket_name = TileBucket.getBucketName()
            tile_index_queue = self.get_ingest_job_tile_index_queue(ingest_job)
        elif ingest_job.ingest_type == IngestJob.VOLUMETRIC_INGEST:
            bucket_name = INGEST_BUCKET 
        else:
            raise ValueError('Unknown ingest_type: {}'.format(ingest_job.ingest_type))
        policy = BossUtil.generate_ingest_policy(ingest_job.id, upload_queue, tile_index_queue, bucket_name, ingest_type=ingest_job.ingest_type)
        ingest_creds.generate_credentials(ingest_job.id, policy.arn)

    def remove_ingest_credentials(self, job_id):
        """
        Remove the ingest credentials for a job
        Args:
            job_id: The id of the ingest job

        Returns:
            status
        """
        # Create the credentials for the job
        ingest_creds = IngestCredentials()
        ingest_creds.remove_credentials(job_id)
        status = BossUtil.delete_ingest_policy(job_id)
        return status
