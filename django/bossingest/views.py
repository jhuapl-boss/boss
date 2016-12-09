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

from bosscore.error import BossError, ErrorCodes
from bossingest.ingest_manager import IngestManager
from bossingest.serializers import IngestJobListSerializer
from bosscore.models import Collection, Experiment, Channel

import bossutils
from bossutils.ingestcreds import IngestCredentials


class IngestJobView(APIView):
    """
    View to create and delete ingest jobs

    """

    def get(self, request, ingest_job_id):
        """

        Args:
            job_id:

        Returns:

        """
        try:
            ingest_mgmr = IngestManager()
            ingest_job = ingest_mgmr.get_ingest_job(ingest_job_id)
            serializer = IngestJobListSerializer(ingest_job)
            print (serializer.data)

            # Start setting up output
            data = {}
            data['ingest_job'] = serializer.data
            if ingest_job.status == 3 or ingest_job.status == 2:
                # Return the information for the deleted job/completed job
                return Response(data, status=status.HTTP_200_OK)
            elif ingest_job.status == 0:
                # check if all message are in the upload queue
                upload_queue = ingest_mgmr.get_ingest_job_upload_queue(ingest_job)
                if upload_queue.queue.attributes.get('ApproximateNumberOfMessages') == ingest_job.tile_count:
                    #generate credentials
                    ingest_job.status = 1
                    ingest_job.save()

            if ingest_job.status == 1:
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
            channel = Channel.objects.get(name=data['ingest_job']["channel"], experiment=experiment)

            resource = {}
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

    def post(self,request):
        """
        Post a new config job and create a new ingest job

        Args:
            ingest_config_data:

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
            ingest_job_id:

        Returns:

        """
        try:
            ingest_mgmr = IngestManager()
            ingest_mgmr.delete_ingest_job(ingest_job_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except BossError as err:
                return err.to_http()
