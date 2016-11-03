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

from django.contrib.auth.models import Group, User

from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse

from guardian.shortcuts import get_objects_for_user, get_perms_for_model, assign_perm, get_users_with_perms, remove_perm


from bosscore.privileges import check_role, BossPrivilegeManager
from bosscore.error import BossHTTPError, ErrorCodes, BossGroupNotFoundError, BossUserNotFoundError
from bosscore.serializers import GroupSerializer, UserSerializer

from bosscore.models import BossGroup


class BossGroupMemberList(APIView):
    """
    Class to get group membership information

    """

    @check_role("resource-manager")
    def get(self, request):
        """
        Gets the membership status of a user for a group
        Args:
           request: Django rest framework request
           group_name: Group name from the request
           user_name: User name from the request

       Returns:
           bool : True if the user is a member of the group

        """
        if 'groupname' in request.query_params:
            groupname = request.query_params['groupname']
        else:
            groupname = None

        if 'username' in request.query_params:
            username = request.query_params['username']
        else:
            username = None

        try:
            if username is None and groupname is None:
                #  Both the user-name and group name is not specified. Return all groups for the logged in user
                list_groups = request.user.groups.values_list('name', flat=True)
                list_groups = [name for name in list_groups]
                data = {"groups": list_groups}
            elif username is not None and groupname is None:
                # username without groupname. Return all groups for this user
                user = User.objects.get(username=username)
                list_groups = user.groups.values_list('name', flat=True)
                list_groups = [name for name in list_groups]
                data = {"groups": list_groups}
            elif username is None and groupname is not None:
                # The group name is specified without the username. Return a list of all users in the group
                group = Group.objects.get(name=groupname)
                list_users = group.user_set.all().values_list('username', flat=True)
                list_users = [name for name in list_users]
                data = {"group-members": list_users}
            else:
                # Both group name and user name are specified. Return the membership status for the user
                group = Group.objects.get(name=groupname)
                usr = User.objects.get(username=username)
                data = group.user_set.filter(id=usr.id).exists()

            return Response(data, status=200)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(groupname)
        except User.DoesNotExist:
            return BossUserNotFoundError(username)


class BossGroupMember(APIView):
    """
    View to add a user to a group

    """

    @check_role("resource-manager")
    def get(self, request, group_name, user_name=None):
        """
        Gets the membership status of a user for a group
        Args:
           request: Django rest framework request
           group_name: Group name from the request
           user_name: User name from the request

       Returns:
           bool : True if the user is a member of the group

        """
        try:
            if user_name is None:
                # Return all users for the group
                group = Group.objects.get(name=group_name)
                list_users = group.user_set.all().values_list('username', flat=True)
                list_users = [name for name in list_users]
                data = {"members": list_users}
            else:
                # Both group name and user name are specified. Return the membership status for the user
                group = Group.objects.get(name=group_name)
                usr = User.objects.get(username=user_name)
                status = group.user_set.filter(id=usr.id).exists()
                data = {"result": status}

            return Response(data, status=200)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def post(self, request, group_name, user_name):
        """
        Adds a user to a group
        Args:
            request: Django rest framework request
            group_name: Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)
                bgroup.group.user_set.add(usr)
                return HttpResponse(status=204)
            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def delete(self, request, group_name, user_name):
        """
        Removes a user from a group
        Args:
            request: Django rest framework request
            group_name:Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)
                bgroup.group.user_set.remove(usr)
                return HttpResponse(status=204)
            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)


class BossGroupMaintainer(APIView):
    """
    View to add a user to a group

    """

    @check_role("resource-manager")
    def get(self, request, group_name, user_name=None):
        """
        Gets the membership status of a user for a group
        Args:
           request: Django rest framework request
           group_name: Group name from the request
           user_name: User name from the request

       Returns:
           bool : True if the user is a member of the group

        """
        try:
            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)
            if user_name is None:

                # Return all maintainers for the group
                list_maintainers = get_users_with_perms(bgroup)
                maintainers = [user.username for user in list_maintainers]
                data = {"maintainers": maintainers}
            else:
                # Both group name and user name are specified. Return the membership status for the user
                usr = User.objects.get(username=user_name)
                status = usr.has_perm("maintain_group", bgroup)
                data = {"result" : status}

            return Response(data, status=200)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def post(self, request, group_name, user_name):
        """
        Adds a user to a group
        Args:
            request: Django rest framework request
            group_name: Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            if user_name is None:
                return BossHTTPError ('Missing username parameter in post.',ErrorCodes.INVALID_URL)

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)

                # assign permissions to the creator of the group
                group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
                for permission in group_perms:
                    assign_perm(permission, usr, bgroup)
                return HttpResponse(status=204)

            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username,'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)

    @check_role("resource-manager")
    def delete(self, request, group_name, user_name):
        """
        Removes a user from a group
        Args:
            request: Django rest framework request
            group_name:Group name from the request
            user_name: User name from the request

        Returns:
            Http status of the request

        """
        try:
            if user_name is None:
                return BossHTTPError ('Missing username parameter in post.',ErrorCodes.INVALID_URL)

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)

            # Check the users permissions.
            if request.user.has_perm("maintain_group", bgroup):
                usr = User.objects.get(username=user_name)
                group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
                status = usr.has_perm('maintain_group',bgroup)

                if status is False:
                    return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                         .format(usr.username, 'maintain_group', group_name),
                                         ErrorCodes.MISSING_PERMISSION)
                else:
                    remove_perm('maintain_group',usr, bgroup)

                return HttpResponse(status=204)
            else:
                return BossHTTPError('The user {} does not have the {} permission on the group {}'
                                     .format(request.user.username, 'maintain_group', group_name),
                                     ErrorCodes.MISSING_PERMISSION)

        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
        except User.DoesNotExist:
            return BossUserNotFoundError(user_name)


class BossUserGroup(APIView):
    """
    View to manage group memberships
    """

    @check_role("resource-manager")
    def get(self, request, group_name=None):
        """
        Get all group s
        Args:
           request: Django rest framework request
           group_name: Group name from the request

       Returns:
            Group if the group exists
        """
        if group_name is not None:
            exists = Group.objects.filter(name=group_name).exists()
            return Response(exists, status=200)
        else:
            # Get all the groups that the logged in user is a member of
            list_member_groups = request.user.groups.values_list('name', flat=True)
            member_groups = [name for name in list_member_groups]

            # Get all groups that the user has maintainer permissions on
            group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
            list_maintainer_groups = get_objects_for_user(request.user, group_perms, klass=BossGroup, any_perm=True)
            maintainer_groups = [bgroup.group.name for bgroup in list_maintainer_groups]

            if 'filter' in request.query_params and request.query_params['filter'] == 'member':
                data = {'groups': member_groups}
                return Response(data, status=200)
            elif 'filter' in request.query_params and request.query_params['filter'] == 'maintainer':
                data = {'groups': maintainer_groups}
                return Response(data, status=200)
            elif 'filter' not in request.query_params:
                all_groups = list(set(member_groups).union(maintainer_groups))
                data = {'groups': all_groups}
            else:
                return BossHTTPError('Unrecogizes value {} in filter. Valid parameters are member or maintainer.',
                                     ErrorCodes.UNABLE_TO_VALIDATE)
            return Response(data, status=200)

    @check_role("resource-manager")
    def post(self, request, group_name):
        """
        Create a new group is the group does not exist
        Args:
            request: Django rest framework request
            group_name: Group name from the request

        Returns:
            Http status of the request

        """
        group, created = Group.objects.get_or_create(name=group_name)
        if not created:
            return BossHTTPError("A group  with name {} already exist".format(group_name), ErrorCodes.GROUP_EXISTS)
        bgroup = BossGroup.objects.create(group=group, creator=request.user)

        # assign permissions to the creator of the group
        group_perms = [perm.codename for perm in get_perms_for_model(BossGroup)]
        for permission in group_perms:
            assign_perm(permission, request.user, bgroup)

        # add the creator to the group
        bgroup.group.user_set.add(request.user)
        return Response(status=201)

    @check_role("resource-manager")
    def delete(self, request, group_name):
        """
        Delete a group. The user has to be an admin or the creator of the group
        Args:
            request: Django rest framework request
            group_name: Group name from the request

        Returns:
            Http status of the request

        """
        try:

            group = Group.objects.get(name=group_name)
            bgroup = BossGroup.objects.get(group=group)
            bpm = BossPrivilegeManager(request.user)
            if request.user == bgroup.creator or bpm.has_role('admin'):
                group.delete()
                return Response(status=204)
            else:
                return BossHTTPError('Groups can only be deleted by the creator or administrator',
                                     ErrorCodes.MISSING_ROLE)
        except Group.DoesNotExist:
            return BossGroupNotFoundError(group_name)
