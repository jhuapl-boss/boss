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

from boss.throttling import RedisMetrics, RedisMetricKey, MetricLimits
from bosscore.constants import ADMIN_USER
from django.contrib.auth.models import User
from bosscore.models import ThrottleThreshold

class Metric(LoginRequiredMixin, APIView):
    """
    View to handle Metric API requests

    Auth is Required
    """
    renderer_classes = (JSONRenderer, )

    def __init__(self):
        """
        Initialize the view with RedisMetrics object
        """
        self.blog = bossLogger()
        self.metrics = RedisMetrics()

    def _get_admin_user(self):
        """
        Lookup the admin user

        Returns: the User object for the Admin user
        """
        return User.objects.get(username=ADMIN_USER)
        
    def _getMetrics(self,metricName):
        """
        Get metrics that match metric name

        Args: 
            metricName (str): name of metric
        
        Returns: result object containing selected metrics
        """
        keys = self.metrics.get_metrics(metricName)
        result = {'metric':metricName, 'values':[]}
        metricKeys = [RedisMetricKey(key=k) for k in keys]
        if metricKeys:
            result = [{ 'name':mk.name, 'value':self.metrics.get_metric(mk), 'units': mk.units, 'type':mk.type } for mk in metricKeys]
        return result

    def _synchLimits(self):
        limits = MetricLimits()
        # convert limits to json
        for t in limits.system:
            units = ThrottleThreshold.METRIC_UNITS_BYTES
            if t == ThrottleThreshold.METRIC_TYPE_COMPUTE:
                units = ThrottleThreshold.METRIC_UNITS_VOXELS
            limit = limits.system[t]
            if not limit:
                limit = -1
            ThrottleThreshold.objects.get_or_create(metric_name='system',metric_type=t,metric_units = units,metric_limit = limit)
        return [limits.system,limits.apis, limits.users]
    
    def _getLimits(self):
        limitObjects = ThrottleThreshold.objects.get()
        return limitObjects

    def get(self, request):
        """
        Handles the get request for metrics
        /metrics/list will list all metric names
        /metrics will return user metrics for the logged in user
            options:
            metric=<name> will return metrics for provided name
            user=<username> will return metrics for provided user

        """
        if self.metrics.conn == None:
            return Response("No redis connection")
        paths = request.path_info.split("/")
        metric = request.GET.get('metric')
        user = request.GET.get('user',str(request.user))
        # determine response
        userIsAdmin = request.user == self._get_admin_user()
        if paths[-1] == 'synch':
            if userIsAdmin:
                return Response(self._synchLimits())
        if paths[-1] == 'list':
            # list all metrics names
            keys = [k.decode('utf8') for k in self.metrics.conn.keys()]
            metrics = set([RedisMetricKey(key=k).name for k in keys])
            return Response(metrics)
        
        if paths[-1] == 'all':
            metric = "*"

        # show specific metric values 
        if not metric:
            metric = user
        metricIsUser = metric == str(request.user)
        userIsAdmin = request.user == self._get_admin_user()
        # make sure only admin user can see other metrics
        if metricIsUser or userIsAdmin:
            return Response(self._getMetrics(metric))
        return Response("Unauthorized request")
