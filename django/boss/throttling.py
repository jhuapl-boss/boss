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

# this method is called repeatedly and requires all limits to have a scalar
def parse_limit(metric,mtype):
    """Convert a textual representation of a number of bytes into an integer

    NOTE: If val is None then None is returned

    Args:
        metric (dict): maps metric types to metric limits
        mtype (str) 

        metric[mtype] has format:
                    <num><scalar> where
                    <num> - is a float
                    <scalar> is one of K, M, G, T, P for
                        kilobytes, megabytes, gigabytes, terabytes, petabytes

    Returns:
        int: Number of bytes
    """
    val = None
    if metric and mtype in metric:
        val = metric[mtype]
    if val is None:
        return None
    # this approach requires a scalar
    num, unit = val[:-1], val[-1]
    val = float(num) * {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
        'T': 1024 * 1024 * 1024 * 1024,
        'P': 1024 * 1024 * 1024 * 1024 * 1024,
    }[unit.upper()]

    return int(val) # Returning an int, as redis works with ints

def _redisKeyNamePattern(metricName):
    """Get a redis search pattern to match metrics by name

    Args: 
        metricName (str): The name of the metric
    
    Returns: format string that can be used as a search pattern
    """
    return "{}*".format(metricName)

class RedisMetricKey(object):
    # redis key for metric encoded with type and units
    def __init__(self, name="system", mtype="ingress", units="bytes", key=None):
        """Initialize key with name, type, and units or from a key
           Args:
            name (str): The name of the metric (system, <api>, or <username>)
            mtype (str): The type of metric e.g. ingress, egress, compute
            units (str): The units of the cost e.g. bytes, cuboids
            key (str): an encoded key
        """
        if key:
            self.fromKey(key)
        else:
            self.name = name
            self.type = mtype
            self.units = units
    def fromKey(self, key):
        """Read encoded key
           Args:
               key (str): encoded key
        """
        parts = key.split("_")
        self.name, self.type, self.units = parts
        return self
    def toKey(self):
        """Encode metric parts
           
           Returns key (str)
        """
        return "_".join([self.name,self.type,self.units])
    
class RedisMetrics(object):
    # NOTE: If there is no throttling redis instance the other methods don't do anything
    # NOTE: External process will reset values to zero when the window expires
    # {obj}_metric = current_cost_in_window
    """
    Object for interacting with a Redis instance storing metric data

    NOTE: If there is no throttling Redis instance the methods don't do anything
    NOTE: An external process will reset the metrics to zero when the time window expires

    Redis data format: {obj}_metric = current_usage_in_window
    """

    def __init__(self):
        self.blog = bossLogger()
        boss_config = bossutils.configuration.BossConfig()
        if len(boss_config['aws']['cache-throttle']) > 0:
            self.conn = redis.StrictRedis(boss_config['aws']['cache-throttle'],
                                          6379,
                                          boss_config['aws']['cache-throttle-db'])
        else:
            self.conn = None
    def get_metrics(self, metricName):
        """Get the metrics that match name
        Args: 
           metricName(str): name of metric

        Returns: list of metricKey objects
        """
        if not self.conn:
           return None
        return [k.decode('utf8') for k in self.conn.keys(pattern=_redisKeyNamePattern(metricName))]

    def get_metric(self, metricKey):
        """Get the current metric value for the given object

        Args:
            metricKey (RedisMetricKey): The metric key object
            

        Returns:
            int: Current metric value or zero if there is no Redis instance or no Redis key
        """
        if self.conn is None:
            return 0

        key = metricKey.toKey()
        resp = self.conn.get(key)
        if resp is None:
            resp = 0
        else:
            resp = int(resp.decode('utf8'))
        return resp

    def add_metric_cost(self, metricKey, val):
        """Increment the current metric value by the given value for the given object

        NOTE: If there is no Redis instance this method doesn't do anything

        Args:
            metricKey (RedisMetricKey): The metric key object 
            val (float|int): Value by which to increase the current metric value
                             NOTE: Value will be converted into an integer
        """
        if self.conn is None:
            return

        key = metricKey.toKey()
        self.conn.incrby(key, int(val))

class MetricLimits(object):
    """Object for reading metric limits

    NOTE: Values are read once from Vault on initialization
    """
    def __init__(self):
        self.blog = bossLogger()
        data = self.read_vault()

        self.system = data.get('system')
        self.apis = data.get('apis')
        self.users = data.get('users')
        self.groups = data.get('groups')
        self.default_user = data.get('default_user')

    @cache(ttl=THROTTLE_VAULT_TIMEOUT)
    def read_vault(self):
        vault = bossutils.vault.Vault()
        data = vault.read('secret/endpoint/throttle', 'config')
        data = json.loads(data)
        return data

    def lookup_system(self, mtype):
        """Return the current metric limit for the entire system by type
        
        Args:
            mtype (str) : The metric type

        Returns:
            int or None
        """
        return parse_limit(self.system, mtype)

    def lookup_api(self, api, mtype):
        """Return the current metric limit for the given API

        Args:
            api (str): Name of the API to get the metric limit for
            mtype (str) : The metric type

        Returns:
            int or None
        """
        return parse_limit(self.apis.get(api),mtype)

    def lookup_user(self, user, mtype):
        """Return the current metric limit for the given user

        A user's metric limit can either be the value given specifically
        to the user or it can be the maximum metric limit for all of the
        groups that the user is a part of.

        Args:
            user (User): Django user object to get the metric limit for
            mtype (str) : The metric type

        Returns:
            int or None
        """
        # User specific settings will override any group based limits
        if user.username in self.users:
            return parse_limit(self.users[user.username],mtype)

        # Find the largest limit for all groups the user is a member of
        limits = [parse_limit(self.groups[group.name],mtype)
                  for group in user.groups.all()
                  if group.name in self.groups]

        if None in limits:
            return None
        elif len(limits) > 0:
            return max(limits)
        else:
            return parse_limit(self.default_user,mtype)

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
        #self.data = RedisMetrics()
        #self.limits = MetricLimits()

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

        #today = datetime.date(datetime.today())
        metric,_ = ThrottleMetric.objects.get_or_create(mtype=mtype, units=units)

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
        self.blog.info("Checking limits for user: {}".format(user.username))
        userMetric = "user:{}".format(user.username)
        threshold, created = ThrottleThreshold.objects.get_or_create(name=userMetric, metric=metric)
        if created:
            threshold.limit = metric.def_user_limit
            threshold.save()
        usage, created = ThrottleUsage.objects.get_or_create(threshold=threshold)
        current = usage.value
        limit = threshold.limit

        if limit > 0 and current > limit:
            self.blog.info("Current use of {} exceeds threshold {}".format(current,limit))
            details['current_metric'] = current
            details['max_metric'] = limit
            self.error(user = user, details = details)

        self.blog.info("Incrementing cost of {} by {}".format(threshold.name, cost))
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
        apiMetric = "api:{}".format(api)
        self.blog.info("Getting threshold for {}".format(apiMetric))
        threshold, created = ThrottleThreshold.objects.get_or_create(name=apiMetric, metric=metric)
        if created:
            threshold.limit = metric.def_api_limit
            threshold.save()

        self.blog.info("Getting current usage for {}".format(apiMetric))
        usage, created = ThrottleUsage.objects.get_or_create(threshold=threshold)
        current = usage.value
        limit = threshold.limit

        if limit > 0 and current > limit:
            details['current_metric'] = current
            details['max_metric'] = limit
            self.error(api = api, details = details)

        self.blog.info("Incrementing {} cost by {}".format(threshold.name, cost))
        usage.value += cost
        usage.save()

    def check_system(self, metric, cost, details):
        """Check to see if the System is currently throttled

        NOTE: This method will increment the current metric value by cost
              if not throttled

        Args:
            metricKey (RedisMetricKey): encoded metric key
            cost (float|int): Cost of the API call being made
            details (dict): General information about the call to be
                            used when notifying administrators

        Raises:
            Throttle: If the system is throttled
        """
        self.blog.info("Checking limits for system")
        threshold, created = ThrottleThreshold.objects.get_or_create(name="system", metric=metric)
        if created:
            threshold.limit = metric.def_system_limit
            threshold.save()

        self.blog.info("Getting current usage for system")
        usage, created = ThrottleUsage.objects.get_or_create(threshold=threshold)
        current = usage.value
        limit = threshold.limit

        if limit > 0 and current > limit:
            details['current_metric'] = current
            details['max_metric'] = limit
            self.error(api = api, details = details)

        self.blog.info("Incrementing {} cost by {}".format(threshold.name, cost))
        usage.value += cost
        usage.save()

