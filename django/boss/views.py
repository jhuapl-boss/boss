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

from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.contrib.auth.mixins import LoginRequiredMixin

from bosscore.error import BossHTTPError, ErrorCodes
from django.conf import settings

import socket

version = settings.BOSS_VERSION

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


class Unsupported(APIView):
    """
    View to handle unsupported API versions

    No Auth Required
    """
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    renderer_classes = (JSONRenderer, )

    def get(self, request):
        """
        Return the unsupported error

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :return:
        """
        return BossHTTPError(" This API version is unsupported. Update to version {}".format(version),
                             ErrorCodes.UNSUPPORTED_VERSION)

    def post(self, request):
        """
        Return the unsupported error

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :return:
        """
        return BossHTTPError(" This API version is unsupported. Update to version {}".format(version),
                             ErrorCodes.UNSUPPORTED_VERSION)

    def delete(self, request):
        """
        Return the unsupported error

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :return:
        """
        return BossHTTPError(" This API version is unsupported. Update to version {}".format(version),
                             ErrorCodes.UNSUPPORTED_VERSION)

    def put(self, request):
        """
        Return the unsupported error

        :param request: DRF Request object
        :type request: rest_framework.request.Request
        :return:
        """
        return BossHTTPError(" This API version is unsupported. Update to version {}".format(version),
                             ErrorCodes.UNSUPPORTED_VERSION)

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View

# import as to deconflict with our Token class
from rest_framework.authtoken.models import Token as TokenModel

class Token(LoginRequiredMixin, View):
    def get(self, request):
        action = request.GET.get('action', None)

        try:
            token = TokenModel.objects.get(user = request.user)
            if action == "Revoke":
                token.delete()
                token = None
        except:
            if action == "Generate":
                token = TokenModel.objects.create(user = request.user)
            else:
                token = None

        if token is None:
            content = ""
            button = "Generate"
        else:
            content = "<textarea>{}</textarea>".format(token)
            button = "Revoke"

        html = """
        <html>
            <head><title>BOSS Token Management</title></head>
            <body>
                    {1}
                    <a href="{0}?action={2}">{2}</a>
            </body>
        </html>
        """.format(request.path_info, content, button)
        return HttpResponse(html)
