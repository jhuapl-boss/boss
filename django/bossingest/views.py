from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from bosscore.error import BossError
from .ingest_manager import IngestManager

# Create your views here.

class IngestJobView(APIView):
    """
    View to create and delete ingest jobs

    """

    def get(self, ingest_job_id):
        """

        Args:
            job_id:

        Returns:

        """
        return Response({})

    def post(self, ingest_config_data):
        """
        Post a new config job and create a new ingest job

        Args:
            ingest_config_data:

        Returns:


        """
        try:
            ingest_mgmr = IngestManager()
            return ingest_mgmr.setup_ingest(self.request.user)
        except BossError as err:
                return err.to_http()

    def delete(self, ingest_job_id):
        """

        Args:
            ingest_job_id:

        Returns:

        """
        try:
            return IngestManager.delete_ingest_job(ingest_job_id)
        except BossError as err:
                return err.to_http()
