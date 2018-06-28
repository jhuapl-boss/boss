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

from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics

from bosscore.error import BossError, ErrorCodes, BossHTTPError
from bossingest.ingest_manager import IngestManager
from bossingest.serializers import IngestJobListSerializer
from bosscore.models import Collection, Experiment, Channel
from bossingest.models import IngestJob
from bossutils.logger import BossLogger

import bossutils
from bossutils.ingestcreds import IngestCredentials
import time
import json


class IngestServiceView(APIView):
    """Parent class for all ingest services that has some built-in methods"""

    def is_user_or_admin(self, request, ingest_job):
        """Method to check if logged in user is the creator of an ingest job or the admin

        Args:
            request:
            ingest_job:

        Returns:

        """
        if ingest_job.creator == request.user or self.get_admin_user() == request.user:
            return True
        else:
            return False

    def get_admin_user(self):
        """Return the admin user"""
        return User.objects.get(username='bossadmin')


class IngestJobView(IngestServiceView):
    """
    View to create and delete ingest jobs

    """
    def list_ingest_jobs(self, request):
        """Method to list all ingest jobs

        Args:
            request(rest_framework.request.Request): the current request

        Returns:
            rest_framework.response.Response
        """
        if self.get_admin_user() == request.user:
            # If admin user, get all Jobs that aren't "cancelled"
            jobs = IngestJob.objects.filter(~Q(status=3))
        else:
            # Just get the active user's Jobs that aren't "cancelled"
            jobs = IngestJob.objects.filter(Q(creator=request.user) & ~Q(status=3))

        list_jobs = []
        for item in jobs:
            config_data = json.loads(item.config_data)
            job = {'id': item.id,
                   'collection': config_data["database"]["collection"],
                   'experiment': config_data["database"]["experiment"],
                   'channel': config_data["database"]["channel"],
                   'created_on': item.start_date,
                   'completed_on': item.end_date,
                   'status': item.status}
            list_jobs.append(job)

        return Response({"ingest_jobs": list_jobs}, status=status.HTTP_200_OK)

    def get(self, request, ingest_job_id=None):
        """
        Join a job with the specified job id or list all job ids if ingest_job_id is omitted
        Args:
            request: Django rest framework request object
            ingest_job_id: Ingest job id

        Returns:
            Ingest job
        """
        try:
            if ingest_job_id is None:
                # If the job ID is empty on a get, you are listing jobs
                return self.list_ingest_jobs(request)

            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.get_ingest_job(ingest_job_id)

            # Check permissions
            if not self.is_user_or_admin(request, ingest_job):
                return BossHTTPError("Only the creator or admin can join an ingest job",
                                     ErrorCodes.INGEST_NOT_CREATOR)

            serializer = IngestJobListSerializer(ingest_job)

            # Start setting up output
            data = {'ingest_job': serializer.data}

            if ingest_job.status == 3:
                # The job has been deleted
                raise BossError("The job with id {} has been deleted".format(ingest_job_id),
                                ErrorCodes.INVALID_REQUEST)
            elif ingest_job.status == 2 or ingest_job.status == 4:
                # Failed job or completed job
                return Response(data, status=status.HTTP_200_OK)

            elif ingest_job.status == 0:
                # Job is still in progress
                # check status of the step function
                session = bossutils.aws.get_session()
                if bossutils.aws.sfn_status(session, ingest_job.step_function_arn) == 'SUCCEEDED':
                    # generate credentials
                    ingest_job.status = 1
                    ingest_job.save()
                    ingest_mgmr.generate_ingest_credentials(ingest_job)
                elif bossutils.aws.sfn_status(session, ingest_job.step_function_arn) == 'FAILED':
                    # This indicates an error in step function
                    raise BossError("Error generating ingest job messages"
                                    " Delete the ingest job with id {} and try again.".format(ingest_job_id),
                                    ErrorCodes.BOSS_SYSTEM_ERROR)

            if ingest_job.status == 1:
                data['ingest_job']['status'] = 1
                ingest_creds = IngestCredentials()
                data['credentials'] = ingest_creds.get_credentials(ingest_job.id)
            else:
                data['credentials'] = None

            data['tile_bucket_name'] = ingest_mgmr.get_tile_bucket()
            data['KVIO_SETTINGS'] = settings.KVIO_SETTINGS
            data['STATEIO_CONFIG'] = settings.STATEIO_CONFIG
            data['OBJECTIO_CONFIG'] = settings.OBJECTIO_CONFIG

            # add the lambda - Possibly remove this later
            config = bossutils.configuration.BossConfig()
            data['ingest_lambda'] = config["lambda"]["page_in_function"]

            # Generate a "resource" for the ingest lambda function to be able to use SPDB cleanly
            collection = Collection.objects.get(name=data['ingest_job']["collection"])
            experiment = Experiment.objects.get(name=data['ingest_job']["experiment"], collection=collection)
            coord_frame = experiment.coord_frame
            channel = Channel.objects.get(name=data['ingest_job']["channel"], experiment=experiment)

            resource={}
            resource['boss_key'] = '{}&{}&{}'.format(data['ingest_job']["collection"],
                                                     data['ingest_job']["experiment"],
                                                     data['ingest_job']["channel"])
            resource['lookup_key'] = '{}&{}&{}'.format(collection.id,
                                                       experiment.id,
                                                       channel.id)

            # The Lambda function needs certain resource properties to perform write ops. Set required things only.
            # This is because S3 metadata is limited to 2kb, so we only set the bits of info needed, and in the lambda
            # Function Populate the rest with dummy info
            # IF YOU NEED ADDITIONAL DATA YOU MUST ADD IT HERE AND IN THE LAMBDA FUNCTION
            resource['channel'] = {}
            resource['channel']['type'] = channel.type
            resource['channel']['datatype'] = channel.datatype
            resource['channel']['base_resolution'] = channel.base_resolution

            resource['experiment'] = {}
            resource['experiment']['num_hierarchy_levels'] = experiment.num_hierarchy_levels
            resource['experiment']['hierarchy_method'] = experiment.hierarchy_method

            resource['coord_frame'] = {}
            resource['coord_frame']['x_voxel_size'] = coord_frame.x_voxel_size
            resource['coord_frame']['y_voxel_size'] = coord_frame.y_voxel_size
            resource['coord_frame']['z_voxel_size'] = coord_frame.z_voxel_size

            # Set resource
            data['resource'] = resource

            return Response(data, status=status.HTTP_200_OK)
        except BossError as err:
                return err.to_http()
        except Exception as err:
            return BossError("{}".format(err), ErrorCodes.BOSS_SYSTEM_ERROR).to_http()

    def post(self, request):
        """
        Post a new config job and create a new ingest job

        Args:
            request: Django Rest framework Request object
            ingest_config_data: COnfiguration data for the ingest job

        Returns:


        """
        ingest_config_data = request.data
        try:
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.setup_ingest(self.request.user.id, ingest_config_data)
            serializer = IngestJobListSerializer(ingest_job)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except BossError as err:
                return err.to_http()

    def delete(self, request, ingest_job_id):
        """

        Args:
            request:
            ingest_job_id:

        Returns:

        """
        try:
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.get_ingest_job(ingest_job_id)

            # Check permissions
            if not self.is_user_or_admin(request, ingest_job):
                return BossHTTPError("Only the creator or admin can cancel an ingest job",
                                     ErrorCodes.INGEST_NOT_CREATOR)

            ingest_mgmr.cleanup_ingest_job(ingest_job, IngestJob.DELETED)
            blog = BossLogger().logger
            blog.info("Deleted Ingest Job {}".format(ingest_job_id))
            return Response(status=status.HTTP_204_NO_CONTENT)

        except BossError as err:
                return err.to_http()


class IngestJobCompleteView(IngestServiceView):
    """
    View to handle "completing" ingest jobs

    """
    def post(self, request, ingest_job_id):
        """
        Signal an ingest job is complete and should be cleaned up by POSTing to this view

        Args:
            request: Django Rest framework Request object
            ingest_job_id: Ingest job id

        Returns:


        """
        try:
            blog = BossLogger().logger
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.get_ingest_job(ingest_job_id)

            if ingest_job.status == IngestJob.PREPARING:
                # If status is Preparing. Deny
                return BossHTTPError("You cannot complete a job that is still preparing. You must cancel instead.",
                                     ErrorCodes.BAD_REQUEST)
            elif ingest_job.status == IngestJob.UPLOADING:
                # Check if user is the ingest job creator or the sys admin
                if not self.is_user_or_admin(request, ingest_job):
                    return BossHTTPError("Only the creator or admin can start verification of an ingest job",
                                         ErrorCodes.INGEST_NOT_CREATOR)

                blog.info('Verifying ingest job {}'.format(ingest_job_id))
                # Start verification process
                if not ingest_mgmr.verify_ingest_job(ingest_job):
                    # Ingest not finished
                    return Response(status=status.HTTP_202_ACCEPTED)

                # Verification successful, fall through to the complete process.

            elif ingest_job.status == IngestJob.COMPLETE:
                # If status is already Complete, just return another 204
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif ingest_job.status == IngestJob.DELETED:
                # Job had already been cancelled
                return BossHTTPError("Ingest job has already been cancelled.",
                                     ErrorCodes.BAD_REQUEST)
            elif ingest_job.status == IngestJob.FAILED:
                # Job had failed
                return BossHTTPError("Ingest job has failed during creation. You must Cancel instead.",
                                     ErrorCodes.BAD_REQUEST)

            # Complete the job.
            blog.info("Completing Ingest Job {}".format(ingest_job_id))

            # Check if user is the ingest job creator or the sys admin
            if not self.is_user_or_admin(request, ingest_job):
                return BossHTTPError("Only the creator or admin can complete an ingest job",
                                     ErrorCodes.INGEST_NOT_CREATOR)

            # Check if any messages remain in the ingest queue
            ingest_queue = ingest_mgmr.get_ingest_job_ingest_queue(ingest_job)
            num_messages_in_queue = int(ingest_queue.queue.attributes['ApproximateNumberOfMessages'])

            # Kick off extra lambdas just in case
            if num_messages_in_queue:
                blog.info("{} messages remaining in Ingest Queue".format(num_messages_in_queue))
                ingest_mgmr.invoke_ingest_lambda(ingest_job, num_messages_in_queue)

                # Give lambda a few seconds to fire things off
                time.sleep(30)

            ingest_mgmr.cleanup_ingest_job(ingest_job, IngestJob.COMPLETE)
            blog.info("Complete successful")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BossError as err:
                return err.to_http()
        except Exception as err:
            blog.error('Caught general exception: {}'.format(err))
            return BossError("{}".format(err), ErrorCodes.BOSS_SYSTEM_ERROR).to_http()


class IngestJobStatusView(IngestServiceView):
    """
    Get the status of an ingest job creation. This return's the status and the ~ number
    of messages in the upload queue

    """

    def get(self, request, ingest_job_id):
        """
        Get the status of an ingest_job and number of messages in the upload queue
        Args:
            request: Django Rest framework object
            ingest_job_id: Ingest job id

        Returns: Status of the job

        """
        try:
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.get_ingest_job(ingest_job_id)

            # Check if user is the ingest job creator or the sys admin
            if not self.is_user_or_admin(request, ingest_job):
                return BossHTTPError("Only the creator or admin can check the status of an ingest job",
                                     ErrorCodes.INGEST_NOT_CREATOR)

            if ingest_job.status == IngestJob.DELETED:
                # Deleted Job
                raise BossError("The job with id {} has been deleted".format(ingest_job_id),
                                ErrorCodes.INVALID_REQUEST)
            else:
                if ingest_job.status == IngestJob.COMPLETE:
                    # Job is Complete so queues are gone
                    num_messages_in_queue = 0
                else:
                    upload_queue = ingest_mgmr.get_ingest_job_upload_queue(ingest_job)
                    num_messages_in_queue = int(upload_queue.queue.attributes['ApproximateNumberOfMessages'])
                    if num_messages_in_queue < ingest_job.tile_count:
                        for n in range(9):
                            num_messages_in_queue += int(upload_queue.queue.attributes['ApproximateNumberOfMessages'])
                        num_messages_in_queue /= 10

                data = {"id": ingest_job.id,
                        "status": ingest_job.status,
                        "total_message_count": ingest_job.tile_count,
                        "current_message_count": int(num_messages_in_queue)}

            return Response(data, status=status.HTTP_200_OK)
        except BossError as err:
                return err.to_http()
        except Exception as err:
            return BossError("{}".format(err), ErrorCodes.BOSS_SYSTEM_ERROR).to_http()

