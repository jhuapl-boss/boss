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
import io
import math

from ingest.core.config import Configuration
from ingest.core.backend import BossBackend

from bossingest.serializers import IngestJobCreateSerializer, IngestJobListSerializer
from bossingest.models import IngestJob

from bosscore.error import BossError, ErrorCodes, BossResourceNotFoundError
from bosscore.models import Collection, Experiment, Channel
from bosscore.lookup import LookUpKey

from ndingest.ndqueue.uploadqueue import UploadQueue
from ndingest.ndqueue.ingestqueue import IngestQueue
from ndingest.ndingestproj.bossingestproj import BossIngestProj
from ndingest.nddynamo.boss_tileindexdb import BossTileIndexDB
from ndingest.ndbucket.tilebucket import TileBucket
from ndingest.util.bossutil import BossUtil

import bossutils
from bossutils.ingestcreds import IngestCredentials

# Get the ingest bucket name from boss.config
config = bossutils.configuration.BossConfig()
ingest_bucket = config["aws"]["ingest_bucket"]
ingest_lambda = config["lambda"]["ingest_function"]

CONNECTER = '&'
MAX_NUM_MSG_PER_FILE = 10000


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
            self.validator.validate_schema()
        except jsonschema.ValidationError as e:
            raise BossError("Schema validation failed! {}".format(e), ErrorCodes.UNABLE_TO_VALIDATE)
        except Exception as e:
            raise BossError(" Could not validate the schema file.{}".format(e), ErrorCodes.UNABLE_TO_VALIDATE)

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
                ingest_queue = self.create_ingest_queue()
                self.job.ingest_queue = ingest_queue.url

                # Call the step function to populate the queue.
                self.job.step_function_arn = self.populate_upload_queue()

                # Compute # of tiles in the job
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

                # tile_bucket = TileBucket(self.job.collection + '&' + self.job.experiment)
                # self.create_ingest_credentials(upload_queue, tile_bucket)

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
            BossError : For serialization errors that occur while creating a ingest job
        """

        ingest_job_serializer_data = {
            'creator': self.owner,
            'collection': self.collection.name,
            'experiment': self.experiment.name,
            'channel': self.channel.name,
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
            'tile_size_x': self.config.config_data["ingest_job"]["tile_size"]["x"],
            'tile_size_y': self.config.config_data["ingest_job"]["tile_size"]["y"],
            'tile_size_z': self.config.config_data["ingest_job"]["tile_size"]["z"],
            'tile_size_t': self.config.config_data["ingest_job"]["tile_size"]["t"],
        }
        serializer = IngestJobCreateSerializer(data=ingest_job_serializer_data)
        if serializer.is_valid():
            ingest_job = serializer.save()
            return ingest_job

        else:
            raise BossError("{}".format(serializer.errors), ErrorCodes.SERIALIZATION_ERROR)

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


    def delete_ingest_job(self, ingest_job):
        """
        Delete an ingest job with a specific id. Note this deletes the queues, credentials and all the remaining tiles
        in the tile bucket for this job id. It does not delete the ingest job datamodel but marks it as deleted.
        Args:
            ingest_job_id: Ingest job  to delete

        Returns:
            Int : ingest job id for the job that was successfully deleted

        Raises:
            BossError : If the the job id is not valid or any exception happens in deletion process

        """
        try:

            # delete ingest job
            proj_class = BossIngestProj.load()
            self.nd_proj = proj_class(ingest_job.collection, ingest_job.experiment, ingest_job.channel,
                                      ingest_job.resolution, ingest_job.id)

            # delete the ingest and upload_queue
            self.delete_upload_queue()
            self.delete_ingest_queue()

            # delete any pending entries in the tile index database and tile bucket
            self.delete_tiles(ingest_job)

            ingest_job.status = 3
            ingest_job.ingest_queue = None
            ingest_job.upload_queue = None
            ingest_job.save()

            # Remove ingest credentials for a job
            self.remove_ingest_credentials(ingest_job_id)

        except Exception as e:
            raise BossError("Unable to delete the upload queue.{}".format(e), ErrorCodes.BOSS_SYSTEM_ERROR)
        except IngestJob.DoesNotExist:
            raise BossError("Ingest job with id {} does not exist".format(ingest_job_id), ErrorCodes.OBJECT_NOT_FOUND)
        return ingest_job_id

    def create_upload_queue(self):
        """
        Create an upload queue for an ingest job using the ndingest library
        Returns:
            UploadQueue : Returns a upload queue object

        """
        UploadQueue.createQueue(self.nd_proj, endpoint_url=None)
        queue = UploadQueue(self.nd_proj, endpoint_url=None)
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

    def delete_ingest_queue(self):
        """
        Delete the current ingest queue
        Returns:
            None

        """
        IngestQueue.deleteQueue(self.nd_proj, endpoint_url=None)

    def get_tile_bucket(self):
        """
        Get the name of the ingest tile bucket

        Returns:
            Str: Name of the Tile bucket

        """
        return TileBucket.getBucketName()

    def populate_upload_queue(self):
        """Execute the populate_upload_queue Step Function

        Returns:
            string: ARN of the StepFunction Execution started

        Raises:
            BossError : if there is no valid ingest job
        """

        if self.job is None:
            raise BossError("Unable to generate upload tasks for the ingest service. Please specify a ingest job",
                            ErrorCodes.UNABLE_TO_VALIDATE)

        ingest_job = self.job

        bosskey = ingest_job.collection + CONNECTER + ingest_job.experiment + CONNECTER + ingest_job.channel
        lookup_key = (LookUpKey.get_lookup_key(bosskey)).lookup_key
        [col_id, exp_id, ch_id] = lookup_key.split('&')
        project_info = [col_id, exp_id, ch_id]

        # DP ???: create IngestJob method that creates the StepFunction arguments?
        args = {
            'job_id': ingest_job.id,
            'upload_queue': ingest_job.upload_queue,
            'ingest_queue': ingest_job.ingest_queue,

            'collection_name': ingest_job.collection,
            'experiment_name': ingest_job.experiment,
            'channel_name': ingest_job.channel,

            'resolution': ingest_job.resolution,
            'project_info': lookup_key.split(CONNECTER),

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
            'z_tile_size': 16,
        }

        session = bossutils.aws.get_session()
        populate_sfn = config['sfn']['populate_upload_queue']
        arn = bossutils.aws.sfn_execute(session, populate_sfn, args)

        return arn

    def generate_upload_tasks(self, job_id=None):
        """
        Generate upload tasks for the ingest job. This creates once task for each tile that has to be uploaded in the
        ingest queue

        Args:
            job_id: Job id of the ingest queue. If not included this takes the current ingest job

        Returns:
            None
        Raises:
            BossError : if there is no valid ingest job

        """

        if job_id is None and self.job is None:
            raise BossError("Unable to generate upload tasks for the ingest service. Please specify a ingest job",
                            ErrorCodes.UNABLE_TO_VALIDATE)
        elif job_id:
            # Using the job id to get the job
            try:
                ingest_job = IngestJob.objects.get(id=job_id)
            except IngestJob.DoesNotExist:
                raise BossError("Ingest job with id {} does not exist".format(job_id), ErrorCodes.RESOURCE_NOT_FOUND)
        else:
            ingest_job = self.job

        # Generate upload tasks for the ingest job
        # Get the project information
        bosskey = ingest_job.collection + CONNECTER + ingest_job.experiment + CONNECTER + ingest_job.channel
        lookup_key = (LookUpKey.get_lookup_key(bosskey)).lookup_key
        [col_id, exp_id, ch_id] = lookup_key.split('&')
        project_info = [col_id, exp_id, ch_id]

        # Batch messages and write to file
        base_file_name = 'tasks_' + lookup_key + '_' + str(ingest_job.id)
        self.file_index = 0

        # open file
        f = io.StringIO()
        header = {'job_id': ingest_job.id, 'upload_queue_url': ingest_job.upload_queue,
                  'ingest_queue_url': ingest_job.ingest_queue}
        f.write(json.dumps(header))
        f.write('\n')
        num_msg_per_file = 0

        for time_step in range(ingest_job.t_start, ingest_job.t_stop, 1):
            # For each time step, compute the chunks and tile keys

            for z in range(ingest_job.z_start, ingest_job.z_stop, 16):
                for y in range(ingest_job.y_start, ingest_job.y_stop, ingest_job.tile_size_y):
                    for x in range(ingest_job.x_start, ingest_job.x_stop, ingest_job.tile_size_x):

                        # compute the chunk indices
                        chunk_x = int(x/ingest_job.tile_size_x)
                        chunk_y = int(y/ingest_job.tile_size_y)
                        chunk_z = int(z/16)

                        # Compute the number of tiles in the chunk
                        if ingest_job.z_stop-z >= 16:
                            num_of_tiles = 16
                        else:
                            num_of_tiles = ingest_job.z_stop-z

                        # Generate the chunk key
                        chunk_key = (BossBackend(self.config)).encode_chunk_key(num_of_tiles, project_info,
                                                                                ingest_job.resolution,
                                                                                chunk_x, chunk_y, chunk_z, time_step)

                        self.num_of_chunks += 1

                        # get the tiles keys for this chunk
                        for tile in range(z, z + num_of_tiles):
                            # get the tile key
                            tile_key = (BossBackend(self.config)).encode_tile_key(project_info, ingest_job.resolution,
                                                                                  chunk_x, chunk_y, tile, time_step)
                            self.count_of_tiles += 1

                            # Generate the upload task msg
                            msg = chunk_key + ',' + tile_key + '\n'
                            f.write(msg)
                            num_msg_per_file += 1

                            # if there are 10 messages in the batch send it to the upload queue.
                            if num_msg_per_file == MAX_NUM_MSG_PER_FILE:
                                fname = base_file_name + '_' + str(self.file_index + 1) + '.txt'
                                self.upload_task_file(fname, f.getvalue())
                                self.file_index += 1
                                f.close()
                                # status = self.send_upload_message_batch(batch_msg)

                                fname = base_file_name + '_' + str(self.file_index+1) + '.txt'
                                f = io.StringIO()
                                header = {'job_id': ingest_job.id, 'upload_queue_url': ingest_job.upload_queue,
                                          'ingest_queue_url':
                                              ingest_job.ingest_queue}
                                f.write(json.dumps(header))
                                f.write('\n')
                                num_msg_per_file = 0

        # Edge case: the last batch size maybe smaller than 10
        if num_msg_per_file != 0:
            fname = base_file_name + '_' + str(self.file_index + 1) + '.txt'
            self.upload_task_file(fname, f.getvalue())
            f.close()
            self.file_index += 1
            num_msg_per_file = 0

        # Update status
        self.job.tile_count = self.count_of_tiles
        self.job.save()

    def upload_task_file(self, file_name_key, data):
        """
        Upload a file with ingest tasks to the ingest s3 bucket
        Args:
            file_name: Filename of the file to upload

        Returns:
            status

        """
        s3 = boto3.resource('s3')
        s3.Bucket(ingest_bucket).put_object(Key=file_name_key, Body=data)
        self.invoke_lambda(file_name_key)

    def invoke_lambda(self, file_name):
        """
        Invoke the lamda per file
        Returns:

        """
        msg_data = {"lambda-name": "upload_enqueue",
                    "upload_bucket_name": ingest_bucket,
                    "filename" : file_name }
        # Trigger lambda to handle it
        client = boto3.client('lambda', region_name=bossutils.aws.get_region())

        response = client.invoke(
            FunctionName=ingest_lambda,
            InvocationType='Event',
            Payload=json.dumps(msg_data).encode())


    @staticmethod
    def create_upload_task_message(job_id, chunk_key, tile_key, upload_queue_arn, ingest_queue_arn):
        """
        Create a dictionary with the upload task message for the tilekey
        Args:
            job_id: Job id of the ingest job
            chunk_key: Chunk key of the chunk in which the tile is
            tile_key: Unique tile key for the tile
            upload_queue_arn: Upload queue url
            ingest_queue_arn: Ingest queue url

        Returns:
            Dict : A single upload task message that corresponds to a tile
        """
        msg = {}
        msg['job_id'] = job_id
        msg['chunk_key'] = chunk_key
        msg['tile_key'] = tile_key
        msg['upload_queue_arn'] = upload_queue_arn
        msg['ingest_queue_arn'] = ingest_queue_arn
        return json.dumps(msg)

    def send_upload_task_message(self, msg):
        """
        Upload one message to the upload queue
        (Note : Currently not used. Replaced with the send_upload_message_batch)
        Args:
            msg: Message to send to the upload queue

        Returns:
            None

        """
        queue = UploadQueue(self.nd_proj, endpoint_url=None)
        queue.sendMessage(msg)

    def send_upload_message_batch(self, list_msg):
        """
        Upload a batch of 10 messages to the upload queue. An error is raised if more than 10 messages are in the batch
        Args:
            list_msg: The list containing the messages to upload

        Returns:
            None

        """
        queue = UploadQueue(self.nd_proj, endpoint_url=None)
        status = queue.sendBatchMessages(list_msg)
        return status

    def delete_tiles(self, ingest_job):
        """
        Delete all remaining tiles from the tile index database and tile bucket
        Args:
            ingest_job: Ingest job model

        Returns:
            None
        Raises:
            BossError : For exceptions that happen while deleting the tiles and index

        """
        try:
            # Get all the chunks for a job
            tiledb = BossTileIndexDB(ingest_job.collection + '&' + ingest_job.experiment)
            tilebucket = TileBucket(ingest_job.collection + '&' + ingest_job.experiment)
            chunks = list(tiledb.getTaskItems(ingest_job.id))

            for chunk in chunks:
                chunk_key = chunk['chunk_key']
                # delete each tile in the chunk
                for key in chunk['tile_uploaded_map']:
                    response = tilebucket.deleteObject(key)
                tiledb.deleteCuboid(chunk['chunk_key'], ingest_job.id)

        except Exception as e:
            raise BossError("Exception while deleteing tiles for the ingest job {}. {}".format(ingest_job.id, e),
                            ErrorCodes.BOSS_SYSTEM_ERROR)

    def create_ingest_credentials(self, upload_queue, tile_bucket):
        """
        Create new ingest credentials for a job
        Args:
            upload_queue : Upload queue for the job
            tile_bucket : Name of the tile bucket for the job
        Returns:
            None

        """
        # Generate credentials for the ingest_job
        # Create the credentials for the job
        # tile_bucket = TileBucket(self.job.collection + '&' + self.job.experiment)
        # self.create_ingest_credentials(upload_queue, tile_bucket)
        ingest_creds = IngestCredentials()
        policy = BossUtil.generate_ingest_policy(self.job.id, upload_queue, tile_bucket)
        ingest_creds.generate_credentials(self.job.id, policy.arn)

    def generate_ingest_credentials(self, ingest_job):
        """
        Create new ingest credentials for a job
        Args:
            upload_queue : Upload queue for the job
            tile_bucket : Name of the tile bucket for the job
        Returns:
            None

        """
        # Generate credentials for the ingest_job
        # Create the credentials for the job
        tile_bucket = TileBucket(ingest_job.collection + '&' + ingest_job.experiment)
        upload_queue = self.get_ingest_job_upload_queue(ingest_job)
        ingest_creds = IngestCredentials()
        policy = BossUtil.generate_ingest_policy(self.job.id, upload_queue, tile_bucket)
        ingest_creds.generate_credentials(self.job.id, policy.arn)

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
