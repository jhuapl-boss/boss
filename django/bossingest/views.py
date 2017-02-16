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
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics

from bosscore.error import BossError, ErrorCodes, BossHTTPError
from bossingest.ingest_manager import IngestManager
from bossingest.serializers import IngestJobListSerializer
from bosscore.models import Collection, Experiment, Channel
from bossingest.models import IngestJob

import bossutils
from bossutils.ingestcreds import IngestCredentials


class IngestJobView(APIView):
    """
    View to create and delete ingest jobs

    """

    def get(self, request, ingest_job_id=None):
        """
        Join a job with the specified job id
        Args:
            request: Django rest framework request object
            ingest_job_id: Ingest job id

        Returns:
            Ingest job
        """
        try:
            # list all ingest jobs if no id is specified
            if ingest_job_id is None:
                jobs = IngestJob.objects.filter(creator=request.user)
                data = {"IDS": [job.id for job in jobs]}
                return Response(data, status=status.HTTP_200_OK)

            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.get_ingest_job(ingest_job_id)

            # Check permissions
            if ingest_job.creator != request.user:
                return BossHTTPError("Forbidden. Cannot join the ingest job ", ErrorCodes.INVALID_REQUEST)

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
                if bossutils.aws.sfn_status(session, ingest_job.step_function_arn) == 'Succeeded':
                    # generate credentials
                    ingest_job.status = 1
                    ingest_job.save()
                    ingest_mgmr.generate_ingest_credentials(ingest_job)
                elif bossutils.aws.sfn_status(session, ingest_job.step_function_arn) == 'Failed':
                    # This indicates an error in step function
                    raise BossError("Error generating ingest job messages"
                                    " Delete the ingest job with id {} and try again.".format(ingest_job_id),
                                    ErrorCodes.BOSS_SYSTEM_ERROR)

            if ingest_job.status == 1:
                data['ingest_job']['status'] = 1
                ingest_creds = IngestCredentials()
                data['credentials'] = ingest_creds.get_credentials(ingest_job.id)
                print(data['credentials'])
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
            channel = Channel.objects.get(name=data['ingest_job']["channel"], experiment=experiment)

            resource={}
            resource['boss_key'] = '{}&{}&{}'.format(data['ingest_job']["collection"],
                                                     data['ingest_job']["experiment"],
                                                     data['ingest_job']["channel"])
            resource['lookup_key'] = '{}&{}&{}'.format(collection.id,
                                                       experiment.id,
                                                       channel.id)
            resource['channel'] = {}
            resource['channel']['name'] = channel.name
            resource['channel']['description'] = ""
            resource['channel']['type'] = channel.type
            resource['channel']['datatype'] = channel.datatype
            resource['channel']['base_resolution'] = channel.base_resolution
            resource['channel']['sources'] = [x.name for x in channel.sources.all()]
            resource['channel']['related'] = [x.name for x in channel.related.all()]
            resource['channel']['default_time_sample'] = channel.default_time_sample

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
            if ingest_job.creator != request.user:
                return BossHTTPError("Forbidden. Cannot join the ingest job ", ErrorCodes.INVALID_REQUEST)

            ingest_mgmr.delete_ingest_job(ingest_job)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except BossError as err:
                return err.to_http()


class IngestJobStatusView(APIView):
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
            if ingest_job.creator != request.user:
                return BossHTTPError("Forbidden.The logged in user is not the job creator", ErrorCodes.INVALID_REQUEST)

            serializer = IngestJobListSerializer(ingest_job)
            print(serializer.data)

            # Start setting up output
            data = {'ingest_job': serializer.data}
            if ingest_job.status == 3:
                # Deleted Job
                raise BossError("The job with id {} has been deleted".format(ingest_job_id),
                                ErrorCodes.INVALID_REQUEST)
            elif ingest_job.status == 2:
                # Failed job
                raise BossError("The job with id {} has failed".format(ingest_job_id),
                                ErrorCodes.INVALID_REQUEST)
            elif ingest_job.status == 0 or ingest_job.status == 0:
                # Complete or preparing
                upload_queue = ingest_mgmr.get_ingest_job_upload_queue(ingest_job)
                num_messages_in_queue = 0
                for n in range(1, 10):
                    num_messages_in_queue += upload_queue.queue.attributes['ApproximateNumberOfMessages']

                num_messages_in_queue /= 10
                data = {"id": ingest_job.id,
                        "status": ingest_job.status,
                        "Total message count": ingest_job.tile_count,
                        "Current message count": num_messages_in_queue}

            return Response(data, status=status.HTTP_200_OK)
        except BossError as err:
                return err.to_http()
        except Exception as err:
            return BossError("{}".format(err), ErrorCodes.BOSS_SYSTEM_ERROR).to_http()


class IngestJobListView(generics.ListCreateAPIView):
    """
    List all coordinate frames
    """
    queryset = IngestJob.objects.all()
    serializer_class = IngestJobListSerializer

    def list(self, request, *args, **kwargs):
        """
        Display all ingest jobs for a user
        Args:
            request: DRF request
            *args:
            **kwargs:

        Returns: A list of job ids for the user

        """
        jobs = IngestJob.objects.filter(creator=request.user)
        data = {"IDS": [job.id for job in jobs]}
        return Response(data)
