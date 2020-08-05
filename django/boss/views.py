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
from bossutils.logger import bossLogger

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

from boss.throttling import RedisMetrics
from bosscore.constants import ADMIN_USER
from django.contrib.auth.models import User

class Metric(LoginRequiredMixin, APIView):

    renderer_classes = (JSONRenderer, )

    def __init__(self):
        self.blog = bossLogger()
        self.metrics = RedisMetrics()

    def get_admin_user(self):
        return User.objects.get(username=ADMIN_USER)

    def getValues(self,keys):
        dates = { k.split("_")[-2] : int(self.metrics.conn.get(k).decode('utf8')) for k in keys }
        total = sum([v for v in dates.values()])
        return { 'dates':dates, 'total':total, 'units': keys[0].split("_")[-1] }
        
    def getMetrics(self,metric):
        keys = [k.decode('utf8') for k in self.metrics.conn.keys(pattern="{}*".format(metric))]
        types = set([k.split("_")[-3] for k in keys])
        result = {'metric':metric}
        for t in types:
            result[t] = self.getValues([k for k in keys if t in k])
        return result

    def get(self, request):
        if self.metrics.conn == None:
            return Response("No redis connection")
        paths = request.path_info.split("/")
        metric = request.GET.get('metric')
        user = request.GET.get('user',str(request.user))
        # show all metrics
        if paths[-1] == 'list':
            keys = [k.decode('utf8') for k in self.metrics.conn.keys()]
            metrics = set(["_".join(k.split("_")[:-3]) for k in keys])
            return Response(metrics)
        else:
            if not metric:
                metric = user
            metricIsUser = metric == str(request.user)
            userIsAdmin = request.user == self.get_admin_user()
            if metricIsUser or userIsAdmin:
                return Response(self.getMetrics(metric))
            return Response("Unauthorized request")
