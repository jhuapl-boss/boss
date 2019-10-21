# Copyright 2019 The Johns Hopkins University Applied Physics Laboratory
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

from rest_framework.exceptions import Throttled

from django.utils.translation import ugettext_lazy as _
from django.conf import settings as django_settings

import json
import bossutils
import redis

def parse_limit(val):
    if val is None:
        return None

    num, unit = val[:-1], val[-1]
    val = float(num) * {
        'K': 1024,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
        'T': 1024 * 1024 * 1024 * 1024,
        'P': 1024 * 1024 * 1024 * 1024 * 1024,
    }[unit.upper()]

    return int(val) # Returning an int, as redis works with ints

class RedisMetrics(object):
    # NOTE: If there is no throttling redis instance the other methods don't do anything
    # NOTE: External process will reset values to zero when the window expires
    # {obj}_metric = current_cost_in_window

    def __init__(self):
        boss_config = bossutils.configuration.BossConfig()
        if len(boss_config['aws']['cache-throttle']) > 0:
            self.conn = redis.StrictRedis(boss_config['aws']['cache-throttle'],
                                          6379,
                                          boss_config['aws']['cache-throttle-db'])
        else:
            self.conn = None

    def get_metric(self, obj):
        if self.conn is None:
            return 0

        key = "{}_metric".format(obj)
        resp = self.conn.get(key)
        if resp is None:
            resp = 0
        else:
            resp = int(resp.decode('utf8'))
        return resp

    def add_metric_cost(self, obj, val):
        if self.conn is None:
            return

        key = "{}_metric".format(obj)
        self.conn.incrby(key, int(val))

class MetricLimits(object):
    def __init__(self):
        vault = bossutils.vault.Vault()
        data = vault.read('secret/endpoint/throttle', 'config')
        data = json.loads(data)

        self.system = data.get('system')
        self.apis = data.get('apis')
        self.users = data.get('users')
        self.groups = data.get('groups')

    def lookup_system(self):
        return parse_limit(self.system)

    def lookup_api(self, api):
        return parse_limit(self.apis.get(api))

    def lookup_user(self, user):
        # User specific settings will override any group based limits
        if user.username in self.users:
            return parse_limit(self.users[user.username])

        # Find the largest limit for all groups the user is a member of
        limits = [parse_limit(self.groups[group.name])
                  for group in user.groups.all()
                  if group.name in self.groups]

        if None in limits:
            return None
        else:
            return max(limits)

class BossThrottle(object):
    user_error_detail = _("User is throttled. Expected available tomorrow.")
    api_error_detail = _("API is throttled. Expected available tomorrow.")
    system_error_detail = _("System is throttled. Expected available tomorrow.")

    # NOTE: Check methods don't add the new cost before checking so as to
    #       still allow an API call that will exceed the limit, in case the
    #       limit would disallow most API calls

    def __init__(self):
        self.data = RedisMetrics()
        self.limits = MetricLimits()

    def error(self, msg):
        raise Throttled(detail = msg)

    def check(self, api, user, cost):
        self.check_user(user, cost)
        self.check_api(api, cost)
        self.check_system(cost)

    def check_user(self, user, cost):
        current = self.data.get_metric(user.username)
        max = self.limits.lookup_user(user)

        if max is None:
            return

        if current > max:
            self.error(self.user_error_detail)

        self.data.add_metric_cost(user.username, cost)

    def check_api(self, api, cost):
        current = self.data.get_metric(api)
        max = self.limits.lookup_api(api)

        if max is None:
            return

        if current > max:
            self.error(self.api_error_detail)

        self.data.add_metric_cost(api, cost)

    def check_system(self, cost):
        current = self.data.get_metric('system')
        max = self.limits.lookup_system()

        if max is None:
            return

        if current > max:
            self.error(self.system_error_detail)

        self.data.add_metric_cost('system', cost)
