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
from bossutils.keycloak import KeyCloakClient

def load_user_role(user, user_name,roles):
    """

    Args:
        user:
        user_name:
        roles:

    Returns:

    """

    kc = KeyCloakClient('BOSS')
    kc.login('admin-cli').json()
    roles = kc.get_realm_roles(user_name,'BOSS')
    print (roles)
    print(user_name)

# Decorators to check that the user has the right role
def check_role(role_name):
    """
    Decorator to check if the user has the required Role.
    Args:
        role_name: Rolename

    Returns:
        BossHTTPError if the user does not have the role

    """
    def check_role_decorator(func):
        @wraps(func)
        def wrapped(self, *args, **kwargs):
            if check_role:
                bpm = BossPrivilegeManager(self.request.user)
                if not bpm.has_role(role_name) and not bpm.has_role('admin'):
                    return BossHTTPError(403, "{} does not have the required role {}"
                                         .format(self.request.user, role_name), 30000)
            return func(self, *args, **kwargs)

        return wrapped
    return check_role_decorator


class BossPrivilegeManager:

    user = None
    roles = set()

    def __init__(self, user_name):
        """
        Initalize the roles for a user
        Args:
            user_name: Username from the request
        """
        self.user = User.objects.get(username=user_name)
        self.get_user_roles()

    def has_role(self, role):
        """
        Check if user has a role
        Args:
            role: Role name

        Returns: True if the user has the role and false otherwise

        """
        return role in self.roles

    def get_user_roles(self):
        """
        Get the roles for the user from the database
        Returns:
            Set containing all the users roles

        """
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
