# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
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

# Redesigned to use ORM for limits. 
# This approach allows for programmatic adjustment of the limits
# 

from rest_framework.exceptions import Throttled
from oidc_auth.util import cache

from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings

import json
import bossutils
import redis

from bosscore.models import ThrottleMetric, ThrottleThreshold, ThrottleUsage
from bossutils.logger import bossLogger
from datetime import date

class MetricDatabase(object):
    """Object wrapper for metric tables
       Provides json object methods for rest API support
       
    """
    SYSTEM_LEVEL_METRIC = 'system'
    API_LEVEL_METRIC = 'api'
    USER_LEVEL_METRIC = 'user'
    def __init__(self):
        self.blog = bossLogger()
        self.blog.info("MetricDatabase object created")

    def getThresholdsAsJson(self):
        limitObjects = ThrottleThreshold.objects.filter()
        return [{ 'metric': limit.name, 
                  'mtype':limit.metric.mtype, 
                  'units':limit.metric.units, 
                  'limit':limit.limit} for limit in limitObjects]
        
    def getAllUsage(self):
        return ThrottleUsage.objects.filter()
    
    def getUsageAsJson(self, name=None):
        usage = []
        if name:
            thresholds = ThrottleThreshold.objects.filter(name=name)
        else:
            thresholds = ThrottleThreshold.objects.filter()
        for t in thresholds:
            usageObjects = ThrottleUsage.objects.filter(threshold=t)
            for u in usageObjects:
                usage.append(u)
        return [{"metric":u.threshold.name,
                 "mtype":u.threshold.metric.mtype,
                 "units":u.threshold.metric.units,
                 "limit":u.threshold.limit,
                 "since":u.since,
                 "value":u.value} for u in usage]

    def encodeMetric(self, level, name=None):
        if level == MetricDatabase.SYSTEM_LEVEL_METRIC:
            return level
        return "{}:{}".format(level,name)
    
    def decodeMetric(self, metricName):
        parts = metricName.split(":")
        if len(parts) > 1:
            return parts[0],parts[1]
        return parts[0], None

    def mapUnits(self, mtype):
        if mtype == ThrottleMetric.METRIC_TYPE_COMPUTE:
            return ThrottleMetric.METRIC_UNITS_CUBOIDS
        return ThrottleMetric.METRIC_UNITS_BYTES

    def getMetricsAsJson(self):
        metricObjects = ThrottleMetric.objects.filter()
        return [{"mtype":m.mtype,
                 "units":m.units,
                 "def_user_limit":m.def_user_limit,
                 "def_api_limit":m.def_api_limit,
                 "def_system_limit":m.def_system_limit} for m in metricObjects]

    def getMetric(self, mtype, units=None):
        if not units:
            units = self.mapUnits(mtype)
        metric,created = ThrottleMetric.objects.get_or_create(mtype=mtype, units=units)
        if created:
            self.blog.info("Created metric {} with units {}".format(metric.mtype, metric.units))
        return metric
    
    def getThreshold(self, name, metric):
        threshold, created = ThrottleThreshold.objects.get_or_create(name=name, metric=metric)
        if created:
            if name.startswith(MetricDatabase.USER_LEVEL_METRIC):
                threshold.limit = metric.def_user_limit
            elif name.startswith(MetricDatabase.API_LEVEL_METRIC):
                threshold.limit = metric.def_api_limit
            else:
                threshold.limit = metric.def_system_limit
            threshold.save()
        return threshold

    def getUsage(self, name, metric):
        threshold = self.getThreshold(name, metric)
        usage,_ = ThrottleUsage.objects.get_or_create(threshold=threshold)
        today = date.today()
        if today.month > usage.since.month:
            usage.value = 0
            usage.since = today
            usage.save()

        return usage
    
    def updateMetrics(self, metricUpdates):
        for m in metricUpdates:
            mtype = m['mtype']
            metric = self.getMetric(mtype=mtype)
            if 'def_user_limit' in m:
                metric.def_user_limit = self.parseLimit(m['def_user_limit'])
            if 'def_api_limit' in m:
                metric.def_api_limit = self.parseLimit(m['def_api_limit'])
            if 'def_system_limit' in m:
                metric.def_system_limit = self.parseLimit(m['def_system_limit'])
            metric.save()

    def updateThreshold(self, name, mtype, limit):
        metric = self.getMetric(mtype)
        threshold = self.getThreshold(name, metric)
        threshold.limit = limit
        threshold.save()

    def parseLimit(self, limit):
        scalar = 1
        if type(limit) is str:
            if not limit.isdigit():
                symbol = limit[-1:].upper()
                if symbol == 'K':
                    scalar = 1024
                elif symbol == 'M':
                    scalar = 1024*1024
                elif symbol == 'G':
                    scalar = 1024*1024*1024
                elif symbol == 'T':
                    scalar = 1024*1024*1024*1024
                limit=limit[:-1].strip()
            limit = int(limit)*scalar
        return limit

    def updateThresholds(self, thresholdUpdates):
        for t in thresholdUpdates:
            name = t['metric']
            mtype = t['mtype']
            limit = self.parseLimit(t['limit'])
            self.updateThreshold(name, mtype, limit)    

class BossThrottle(object):
    """Object for checking if a given API call is throttled

    NOTE: The check_* methods don't add the new cost before checking
          if the current call is throttled, so as to still allow an API
          call that will exceed the limit, in case the limit would
          disallow most API calls

    Attributes:
        user_error_detail (str): Error message if the user is throttled
        api_error_detail (str): Error message if the API is throttled
        system_error_detail (str): Error message if the whole system is throttled
    """
    user_error_detail = _("User is throttled. Expected available tomorrow.")
    api_error_detail = _("API is throttled. Expected available tomorrow.")
    system_error_detail = _("System is throttled. Expected available tomorrow.")

    def __init__(self):
        self.blog = bossLogger()
        self.metricdb = MetricDatabase()
        boss_config = bossutils.configuration.BossConfig()
        self.topic = boss_config['aws']['prod_mailing_list']
        self.fqdn = boss_config['system']['fqdn']

    def error(self, user=None, api=None, system=None, details=None):
        """Method for notifying admins and raising a Throttle exception

        Notifications are send to the Production Mailing List SNS topic

        Args:
            user (optional[str]): Name of the user, if the user is throttled
            api (optional[str]): Name of the API, if the API is throttled
            system (optional[bool]): If the system is throttled
            details (dict): Information about the API call that will be included
                            in the notification to the administrators

        Raises:
            Throttle: Exception with generic information on why the call was throttled
        """
        if user:
            ex_msg = self.user_error_detail
            sns_msg = "Throttling user '{}': {}".format(user.username, json.dumps(details))
        elif api:
            ex_msg = self.api_error_detail
            sns_msg = "Throttling API '{}': {}".format(api, json.dumps(details))
        elif system:
            ex_msg = self.system_error_detail
            sns_msg = "Throttling system: {}".format(json.dumps(details))

        client = bossutils.aws.get_session().client('sns')
        client.publish(TopicArn = self.topic,
                       Subject = 'Boss Request Throttled',
                       Message = sns_msg)

        raise Throttled(detail = ex_msg)

    def check(self, api, mtype, user, cost, units):
        """Check to see if the given API call is throttled

        This is the main BossThrottle method and will call the other check_* methods

        Args:
            api (str): Name of the API call being made
            user (User): Django user making the request
            cost (float|int): Cost of the API call being made

        Raises:
            Throttle: If the call is throttled
        """
        details = {'api': api, 'user': user.username, 'cost': cost, 'fqdn': self.fqdn}
        self.blog.info("Checking for throttling: {},{},{},{},{},{}".format(api,mtype,user.username,cost,units,self.fqdn))

        metric = self.metricdb.getMetric(mtype, units)

        self.check_user(user, metric, cost, details)
        self.check_api(api, metric, cost, details)
        self.check_system(metric, cost, details)

    def check_user(self, user, metric, cost, details):
        """Check to see if the user is currently throttled

        NOTE: This method will increment the current metric value by cost
              if not throttled

        Args:
            user (User): Django user making the request
            metricKey (RedisMetricKey): encoded metric
            cost (float|int): Cost of the API call being made
            details (dict): General information about the call to be
                            used when notifying administrators

        Raises:
            Throttle: If the user is throttled
        """
        userMetric = self.metricdb.encodeMetric(MetricDatabase.USER_LEVEL_METRIC, user.username)
        self.blog.info("Checking limits for user: {}".format(userMetric))
        usage = self.metricdb.getUsage(userMetric, metric)
        current = usage.value
        limit = usage.threshold.limit

        if limit > 0 and current > limit:
            self.blog.info("Current use of {} exceeds threshold {}".format(current,limit))
            details['current_metric'] = current
            details['max_metric'] = limit
            self.error(user = user, details = details)

        self.blog.info("Incrementing cost of {} by {}".format(usage.threshold.name, cost))
        usage.value += cost
        usage.save()

    def check_api(self, api, metric, cost, details):
        """Check to see if the API is currently throttled

        NOTE: This method will increment the current metric value by cost
              if not throttled

        Args:
            api (str): Name of the API call being made
            metricKey (RedisMetricKey): encoded metric key
            cost (float|int): Cost of the API call being made
            details (dict): General information about the call to be
                            used when notifying administrators

        Raises:
            Throttle: If the API is throttled
        """
        apiMetric = self.metricdb.encodeMetric(MetricDatabase.API_LEVEL_METRIC, api)
        usage = self.metricdb.getUsage(apiMetric, metric)
        current = usage.value
        limit = usage.threshold.limit

        if limit > 0 and current > limit:
            details['current_metric'] = current
            details['max_metric'] = limit
            self.error(api = api, details = details)

        self.blog.info("Incrementing {} cost by {}".format(usage.threshold.name, cost))
        usage.value += cost
        usage.save()

    def check_system(self, metric, cost, details):
        """Check to see if the System is currently throttled

        NOTE: This method will increment the current metric value by cost
              if not throttled

        Args:
            metric (ThrottleMetric): metric object
            cost (int): Cost of the API call being made
            details (dict): General information about the call to be
                            used when notifying administrators

        Raises:
            Throttle: If the system is throttled
        """
        self.blog.info("Checking limits for system")
        systemMetric = self.metricdb.encodeMetric(MetricDatabase.SYSTEM_LEVEL_METRIC)
        usage = self.metricdb.getUsage(systemMetric, metric)
        current = usage.value
        limit = usage.threshold.limit

        if limit > 0 and current > limit:
            details['current_metric'] = current
            details['max_metric'] = limit
            self.error(system = MetricDatabase.SYSTEM_LEVEL_METRIC, details = details)

        self.blog.info("Incrementing {} cost by {}".format(usage.threshold.name, cost))
        usage.value += cost
        usage.save()