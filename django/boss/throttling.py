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

import bossutils

import redis

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
        return resp

    def add_metric_cost(self, obj, val):
        if self.conn is None:
            return

        key = "{}_metric".format(obj)
        self.conn.incrby(key, val)

class BossThrottle(object):
    user_error_detail = _("User is throttled. Expected available tomorrow.")
    api_error_detail = _("API is throttled. Expected available tomorrow.")
    system_error_detail = _("System is throttled. Expected available tomorrow.")

    USER_DEFAULT_MAX = 100 * 1024 * 1024 # 100 MB / day
    API_DEFAULT_MAX = 1 * 1024 * 1024 * 1024 # 1 GB / day
    SYSTEM_DEFAULT_MAX = 10 * 1024 * 1024 * 1024 # 10 GB / day

    # NOTE: Check methods don't add the new cost before checking so as to
    #       still allow an API call that will exceed the limit, in case the
    #       limit would disallow most API calls

    # TODO: Figure out how to have more dynamic rules

    def __init__(self):
        self.data = RedisMetrics()

    def error(self, msg):
        raise Throttled(detail = msg)

    def check(self, api, user, cost):
        self.check_user(user, cost)
        self.check_api(api, cost)
        self.check_system(cost)

    def check_user(self, user, cost)
        current = self.data.get_metric(user)
        max = self.USER_DEFAULT_MAX

        if current > max:
            self.error(self.user_error_detail)

        self.data.add_metric_cost(user, cost)

    def check_api(self, api, cost)
        current = self.data.get_metric(api)
        max = self.API_DEFAULT_MAX

        if current > max:
            self.error(self.api_error_detail)

        self.data.add_metric_cost(api, cost)

    def check_system(self, cost)
        current = self.data.get_metric('system')
        max = self.SYSTEM_DEFAULT_MAX

        if current > max:
            self.error(self.system_error_detail)

        self.data.add_metric_cost('system', cost)
