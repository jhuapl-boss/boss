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
from functools import wraps
from bosscore.error import BossHTTPError
from .models import BossRole

BOSS_PRIVILEGES = {
    'admin' : ['create user', 'delete user', 'assign user roles', 'revoke user roles', 'reset password', 'create group',
               'list groups', 'delete group', 'assign user to group', 'assign user to group','remove user from group',
               'assign group to a resource', 'create resource','delete resource'],
    'user-manager': [ 'create user', 'delete user', 'assign user roles', 'revoke user roles', 'reset password'],
    'resource-manager': ['create group', 'delete group', 'assign user to group', 'remove user from group',
                        'assign group to a resource', 'create resource','delete resource'],
    'default': ['list groups']
    }


# Decorators to check that the user has the right role
def check_role(role_name):
    """

    Args:
        role_name:

    Returns:

    """
    def check_role_decorator(func):
        @wraps(func)
        def wrapped(self, *args, **kwargs):
            if check_role:
                bpm = BossPrivilegeManager(self.request.user)
                if not bpm.has_role(role_name) and not bpm.has_role('admin'):
                    return BossHTTPError(404, "{} does not have the required role {}"
                                         .format(self.request.user, role_name), 30000)
            return func(self, *args, **kwargs)

        return wrapped
    return check_role_decorator

class BossPrivilegeManager:

    user = None
    privileges = set()
    roles = set()

    def __init__(self, user_name, roles=None):
        # If roles are not specified, get the user roles from the database
        self.user = User.objects.get(username= user_name)
        self.get_user_roles()
        #self.get_user_privileges()

    def has_privilege(self, privilege):
        return privilege in self.privileges

    def has_role(self, role):
        return role in self.roles

    def get_user_roles(self):
        self.roles = set()
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
            self.privileges |= set(BOSS_PRIVILEGES[role])
        return self.privileges


