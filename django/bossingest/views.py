from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from bosscore.error import BossError
from bossingest.ingest_manager import IngestManager
from bossingest.serializers import IngestJobListSerializer

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
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BossError as err:
                return err.to_http()


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
