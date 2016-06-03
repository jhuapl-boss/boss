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
from django.contrib.auth.models import User
from .models import BossRole

BOSS_PRIVILEGES = {
    'admin' : ['create user', 'delete user', 'assign user roles', 'revoke user roles', 'reset password', 'create group',
               'list groups', 'delete group', 'assign user to group', 'assign user to group','remove user from group',
               'assign group to a resource', 'create resource'],
    'user-manager': [ 'create user', 'delete user', 'assign user roles', 'revoke user roles', 'reset password'],
    'resource-manager': '[create group, delete group, assign user to group, remove user from group, '
                        'assign group to a resource, create resource]',
    'default': 'list groups'
    }


class BossPrivilegeManager:

    user = None
    privileges = set()
    roles = set()

    def __init__(self, user_name, roles=None):
        # If roles are not specified, get the user roles from the database
        self.user = User.objects.get(username= user_name)
        self.get_user_roles()



    def has_privilege(self, privilege):
        return privilege in self.privileges

    def get_user_roles(self):
        self.roles.add('default')
        try:
            all_roles = BossRole.objects.filter(user=self.user)
            for role in all_roles:
                self.roles.add(role.role)
            return self.roles
        except BossRole.DoesNotExist:
            # User only has the default user role
            return self.roles

    def get_user_privileges(self):
        roles = self.get_user_roles()
        for role in roles:
            print(BOSS_PRIVILEGES[role])
