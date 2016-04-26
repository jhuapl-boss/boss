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

from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from rest_framework.authtoken.models import Token

class Token(LoginRequiredMixin, View):
    def get(self, request):
        try:
            token = Token.objects.get(user = request.user)
            content = "<textarea>{}</textarea>".format(token)
            button = "Revoke"
        except:
            content = ""
            button = "Create"

        html = """
        <html>
            <head><title>BOSS Token Management</title></head>
            <body>
                <form method="POST" enctype="multipart/form-data">
                    {}
                    <button>{}</button>
                </form>
            </body>
        </html>
        """.format(content, button)
        return HttpResponse(html)

    def post(self, request):
        try:
            token = Token.objects.get(user = request.user)
            token.delete()
        except:
            token = Token.objects.create(user = request.user)

        return HttpResponseRedirect("/token/")
