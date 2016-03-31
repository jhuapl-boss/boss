from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.contrib.auth.mixins import LoginRequiredMixin

import socket


class Ping(APIView):
    """
    View to provide a basic health/connectivity check

    No Auth Required
    """
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer, )

    def get(self, request):
        """
        Return the server IP

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :return:
        """
        content = {'ip': socket.gethostbyname(socket.gethostname())}
        return Response(content)

class Test(LoginRequiredMixin, APIView):
    authentication_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        content = {"username": request.user.username}
        return Response(content)
