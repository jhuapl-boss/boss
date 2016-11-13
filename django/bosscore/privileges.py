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
from django.contrib.auth.models import User, Group
from functools import wraps
from bosscore.error import BossHTTPError, ErrorCodes
from bosscore.serializers import BossRoleSerializer
from .models import BossRole, BossGroup

VALID_ROLES = ('admin', 'user-manager', 'resource-manager')

def load_user_roles(user, roles):
    """
        Loads user roles from keycloak to django on user login
        Args:
            user: (Not user. Could remove)
            user_name: user_name of user
            roles: List of keycloak roles

        Returns: None

        """
    # Remove any existing roles that are not asxsigned to the user
    existing_roles = []
    try:
        for role in BossRole.objects.filter(user = user.pk):
            if role.role not in roles:
                role.delete()
            else:
                existing_roles.append(role.role)
    except BossRole.DoesNotExist:
        pass

    # Assign any new roles
    for role in roles:
        if role in VALID_ROLES and role not in existing_roles:
            data = {'user': user.pk, 'role': role}
            serializer = BossRoleSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                # TODO: Clean up error handling for this method
                return BossHTTPError("{}".format(serializer.errors), ErrorCodes.SERIALIZATION_ERROR)

    groups = user.groups.all()
    for name in [user.username + '-primary', 'bosspublic']:
        group, created = Group.objects.get_or_create(name=name)
        if group not in groups:
            user.groups.add(group)

        # primary and bosspublic are owned by the admin
        if created:
            admin_user = User.objects.get(username='bossadmin')
            bgroup = BossGroup.objects.create(group=group, creator=admin_user)

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
                    return BossHTTPError("{} does not have the required role {}"
                                         .format(self.request.user, role_name), ErrorCodes.MISSING_ROLE)
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
