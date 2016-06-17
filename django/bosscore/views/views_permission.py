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

import json
from django.db import transaction
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from bosscore.models import Collection, Experiment, ChannelLayer
from bosscore.permissions import BossPermissionManager
from bosscore.error import BossHTTPError, BossError
from bosscore.privileges import check_role

class ResourceUserPermission(APIView):
    """
    View to assign Permissions to resource instances

    """

    @staticmethod
    def get_object(collection, experiment=None, channel_layer=None):
        """ Return the resource from the request

        Args:
            collection: Collection name from the request
            experiment: Experiment name from the request
            channel_layer: Channel or layer name

        Returns:
            Instance of the resource from the request

        """
        try:
            if collection and experiment and channel_layer:
                # Channel/ Layer specified
                collection_obj = Collection.objects.get(name=collection)
                experiment_obj = Experiment.objects.get(name=experiment, collection=collection_obj)
                obj = ChannelLayer.objects.get(name=channel_layer, experiment=experiment_obj)

            elif collection and experiment:
                # Experiment
                collection_obj = Collection.objects.get(name=collection)
                obj = Experiment.objects.get(name=experiment, collection=collection_obj)

            elif collection:
                obj = Collection.objects.get(name=collection)
            else:
                return BossHTTPError(404, "Unable to process the request", 30000)

            return obj
        except Collection.DoesNotExist:
            raise BossError(404, "Collection  with name {} is not found".format(collection), 30000)
        except Experiment.DoesNotExist:
            raise BossError(404, "Experiment  with name {} is not found".format(experiment), 30000)
        except ChannelLayer.DoesNotExist:
            raise BossError(404, "A Channel or layer  with name {} is not found".format(channel_layer), 30000)

    @check_role("resource-manager")
    def get(self, request, group_name, collection, experiment=None, channel_layer=None):
        """Return a list of permissions

        Get the list of the permissions for a group on a resource. These determine the access for the users
        in the group on the resource

        Args:
           request: Django Rest framework request
           group_name: Group name of an existing group
           collection: Collection name from the request
           experiment: Experiment name from the request
           channel_layer: Channel or Layer name from the request

       Returns:
           List of permissions

        """
        try:

            obj = self.get_object(collection, experiment, channel_layer)
            perm = BossPermissionManager.get_permissions_group(group_name, obj)
            data = {'group': group_name, 'permissions': perm}
            return Response(data, status=status.HTTP_201_CREATED, content_type='application/json')

        except Group.DoesNotExist:
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
        except Permission.DoesNotExist:
            return BossHTTPError(404, "Invalid permissions in post".format(request.data['permissions']), 30000)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def post(self, request, group_name, collection, experiment=None, channel_layer=None):
        """ Add permissions to a resource

        Add new permissions for a existing group and resource object

        Args:
            request: Django rest framework request
            group_name: Group name of an existing group
            collection: Collection name from the request
            experiment: Experiment name from the request
            channel_layer: Channel or layer name from the request

        Returns:
            Http status code

        """
        # print(request.data)
        # perm = request.data.copy()
        # perm = dict(perm)
        # print(type(perm['permissions']))

        if 'permissions' not in request.data:
            return BossHTTPError(404, "Permission are not included in the request", 30000)
        else:
            perm_list = dict(request.data)['permissions']

        try:
            obj = self.get_object(collection, experiment, channel_layer)
            if request.user.has_perm("assign_group", obj):
                BossPermissionManager.add_permissions_group(group_name, obj, perm_list)
                return Response(status=status.HTTP_201_CREATED)
            else:
                return BossHTTPError(404, "The user {} needs the 'assign group' permission for this request".
                                     format(request.user), 30000)

        except Group.DoesNotExist:
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
        except Permission.DoesNotExist:
            return BossHTTPError(404, "Invalid permissions in post".format(request.data['permissions']), 30000)
        except BossError as err:
            return err.to_http()

    @transaction.atomic
    @check_role("resource-manager")
    def delete(self, request, group_name, collection, experiment=None, channel_layer=None):
        """ Delete permissions for a resource object

       Remove specific permissions for a existing group and resource object

       Args:
            request: Django rest framework request
            group_name: Group name of an existing group
            collection: Collection name from the request
            experiment: Experiment name from the request
            channel_layer: Channel or layer name from the request
        Returns:
            Http status code

        """
        if 'permissions' not in request.data:
            return BossHTTPError(404, "Permission are not included in the request", 30000)
        else:
            perm_list = dict(request.data)['permissions']

        try:
            obj = self.get_object(collection, experiment, channel_layer)
            if request.user.has_perm("remove_group", obj):
                BossPermissionManager.delete_permissions_group(group_name, obj, perm_list)
                return Response(status=status.HTTP_200_OK)
            else:
                return BossHTTPError(404, "The user {} needs the 'remove group' permission for this request".
                                     format(request.user), 30000)

        except Group.DoesNotExist:
            return BossHTTPError(404, "A group  with name {} is not found".format(group_name), 30000)
        except Permission.DoesNotExist:
            return BossHTTPError(404, "Invalid permissions in post".format(request.data['permissions']), 30000)
        except BossError as err:
            return err.to_http()
