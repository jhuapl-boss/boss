#/bin/sh
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

# Shell script to simplify the process of generating new migrations for
# any of the Boss applications. Using the boss.settings.base settings
# because the boss.settings.production will try to connect to Vault
# and read the /etc/boss/boss.config file

DJANGO_SETTINGS_MODULE=boss.settings.base \
    python3 manage.py makemigrations \
    bosscore \
    bossingest \
    bossmeta \
    bossobject \
    bossspatialdb \
    mgmt \
    sso
