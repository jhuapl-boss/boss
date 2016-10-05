from django.shortcuts import render
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from bosscore.error import BossError, ErrorCodes
from bossingest.ingest_manager import IngestManager
from bossingest.serializers import IngestJobListSerializer
from bosscore.models import Collection, Experiment, ChannelLayer

import bossutils
from bossutils.ingestcreds import IngestCredentials
# Create your views here.

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

            # Start setting up output
            data = {}
            data['ingest_job'] = serializer.data
            data['tile_bucket_name'] = ingest_mgmr.get_tile_bucket()
            data['KVIO_SETTINGS'] = settings.KVIO_SETTINGS
            data['STATEIO_CONFIG'] = settings.STATEIO_CONFIG
            data['OBJECTIO_CONFIG'] = settings.OBJECTIO_CONFIG
            # add the credentials
            ingest_creds = IngestCredentials()
            data['credentials'] = ingest_creds.get_credentials(ingest_job.id)

            # add the lambda - Possibly remove this later
            config = bossutils.configuration.BossConfig()
            data['ingest_lambda'] = config["lambda"]["page_in_function"]

            # Generate a "resource" for the ingest lambda function to be able to use SPDB cleanly
            collection = Collection.objects.get(name=data['ingest_job']["collection"])
            experiment = Experiment.objects.get(name=data['ingest_job']["experiment"], collection=collection)
            channel_layer = ChannelLayer.objects.get(name=data['ingest_job']["channel_layer"], experiment=experiment)

            resource = {}
            resource['boss_key'] = ['{}&{}&{}'.format(data['ingest_job']["collection"],
                                                      data['ingest_job']["experiment"],
                                                      data['ingest_job']["channel_layer"])]
            resource['lookup_key'] = ['{}&{}&{}'.format(collection.id,
                                                        experiment.id,
                                                        channel_layer.id)]
            resource['collection'] = {}
            resource['collection']['name'] = collection.name
            resource['collection']['description'] = collection.description
            resource['coord_frame'] = {}
            resource['coord_frame']['name'] = ""
            resource['coord_frame']['description'] = ""
            resource['coord_frame']['x_start'] = 0
            resource['coord_frame']['x_stop'] = 0
            resource['coord_frame']['y_start'] = 0
            resource['coord_frame']['y_stop'] = 0
            resource['coord_frame']['z_start'] = 0
            resource['coord_frame']['z_stop'] = 0
            resource['coord_frame']['x_voxel_size'] = 0
            resource['coord_frame']['y_voxel_size'] = 0
            resource['coord_frame']['z_voxel_size'] = 0
            resource['coord_frame']['voxel_unit'] = "nanometers"
            resource['coord_frame']['time_step'] = 0
            resource['coord_frame']['time_step_unit'] = "nm"
            resource['experiment'] = {}
            resource['experiment']['name'] = experiment.name
            resource['experiment']['description'] = experiment.description
            resource['experiment']['num_hierarchy_levels'] = experiment.num_hierarchy_levels
            resource['experiment']['hierarchy_method'] = experiment.hierarchy_method
            resource['experiment']['max_time_sample'] = experiment.max_time_sample
            resource['channel_layer'] = {}
            resource['channel_layer']['name'] = channel_layer.name
            resource['channel_layer']['description'] = channel_layer.description
            resource['channel_layer']['is_channel'] = channel_layer.is_channel
            resource['channel_layer']['datatype'] = channel_layer.datatype

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
