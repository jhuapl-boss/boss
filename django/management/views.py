from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django import forms

from sso.views.views_user import BossUser, BossUserRole
from bosscore.views.views_group import BossUserGroup, BossGroupMaintainer, BossGroupMember
from bosscore.views.views_resource import CollectionList, CollectionDetail
from bosscore.views.views_resource import ExperimentList, ExperimentDetail
from bosscore.views.views_resource import CoordinateFrameList, CoordinateFrameDetail
from bosscore.views.views_resource import ChannelList, ChannelDetail
from bossmeta.views import BossMeta

# import as to deconflict with our Token class
from rest_framework.authtoken.models import Token as TokenModel

class Home(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse(render_to_string('base.html'))

class UserForm(forms.Form):
    username = forms.CharField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    verify_password = forms.CharField(widget=forms.PasswordInput())

class Users(LoginRequiredMixin, View):
    def get(self, request):
        boss = BossUser()
        boss.request = request

        delete = request.GET.get('delete')
        if delete:
            resp = boss.delete(request, delete)
            if resp.status_code != 204:
                return resp
            return HttpResponseRedirect('/v0.7/mgmt/users/')

        users = boss.get(request) # search query parameter will be automatically passed
        if users.status_code != 200:
            return users # should reformat to a webpage

        users = users.data
        args = {
            'users': users,
            'form': UserForm(),
        }
        return HttpResponse(render_to_string('users.html', args, RequestContext(request)))

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] != form.cleaned_data['verify_password']:
                pass # ERROR

            username = form.cleaned_data['username']

            boss = BossUser()
            boss.request = request # needed for check_role() to work
            boss.request.data = request.POST # simulate the DRF request object
            resp = boss.post(request, username)
            if resp.status_code != 201:
                return resp # should reformat to a webpage

            return HttpResponseRedirect('/v0.7/mgmt/users/')

class RoleForm(forms.Form):
    role = forms.ChoiceField(choices=[(c,c) for c in ['', 'user-manager', 'resource-manager']])

class User(LoginRequiredMixin, View):
    def get(self, request, username):
        # DP NOTE: Using BossUserRole because BossUser doesn't add anything
        #          that is useful to display
        boss = BossUserRole()
        boss.request = request # needed for check_role() to work

        remove = request.GET.get('remove')
        if remove is not None:
            resp = boss.delete(request, username, remove)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            #return redirect('/v0.7/mgmt/user/' + username)
            return HttpResponseRedirect('/v0.7/mgmt/user/' + username)

        roles = boss.get(request, username)

        if roles.status_code != 200:
            return roles # should reformat to a webpage

        roles = roles.data

        args = {
            'username': username,
            'roles': roles,
            'form': RoleForm(),
            #'debug': user,
        }
        return HttpResponse(render_to_string('user.html', args, RequestContext(request)))

    def post(self, request, username):
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']

            boss = BossUserRole()
            boss.request = request # needed for check_role() to work
            resp = boss.post(request, username, role)
            if resp.status_code != 201:
                return resp # should reformat to a webpage

            return HttpResponseRedirect('/v0.7/mgmt/user/' + username)

class Token(LoginRequiredMixin, View):
    def get(self, request):
        try:
            token = TokenModel.objects.get(user = request.user)
            button = "Revoke Token"
        except:
            token = None
            button = "Generate Token"

        args = {
            'username': request.user,
            'token': token,
            'button': button,
        }
        return HttpResponse(render_to_string('token.html', args, RequestContext(request)))

    def post(self, request):
        try:
            token = TokenModel.objects.get(user = request.user)
            token.delete()
        except:
            token = TokenModel.objects.create(user = request.user)

        return HttpResponseRedirect('/v0.7/mgmt/token/')

class GroupForm(forms.Form):
    group_name = forms.CharField()

class Groups(LoginRequiredMixin, View):
    def get(self, request):
        boss = BossUserGroup()
        boss.request = request

        delete = request.GET.get('delete')
        if delete:
            resp = boss.delete(request, delete)
            if resp.status_code != 204:
                return resp
            return HttpResponseRedirect('/v0.7/mgmt/groups/')

        boss.request.query_params = {}
        # can only modify groups the user is a maintainer of
        boss.request.query_params['filter'] = 'maintainer' 
        groups = boss.get(request)
        if groups.status_code != 200:
            return groups

        args = {
            'groups': groups.data['groups'],
            'form': GroupForm(),
        }
        return HttpResponse(render_to_string('groups.html', args, RequestContext(request)))

    def post(self, request):
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']

            boss = BossUserGroup()
            boss.request = request # needed for check_role() to work
            resp = boss.post(request, group_name)
            if resp.status_code != 201:
                return resp # should reformat to a webpage

            return HttpResponseRedirect('/v0.7/mgmt/groups/')

class GroupMemberForm(forms.Form):
    user = forms.CharField()
    role = forms.ChoiceField(choices=[(c,c) for c in ['', 'member', 'maintainer', 'member+maintainer']])

class Group(LoginRequiredMixin, View):
    def get(self, request, group_name):
        boss_memb = BossGroupMember()
        boss_memb.request = request
        members = boss_memb.get(request, group_name)
        if members.status_code != 200:
            return members
        members = members.data['members']

        remove = request.GET.get('rem_memb')
        if remove is not None:
            resp = boss_memb.delete(request, group_name, remove)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/group/' + group_name)

        boss_maint = BossGroupMaintainer()
        boss_maint.request = request
        maintainers = boss_maint.get(request, group_name)
        if maintainers.status_code !=200:
            return maintainers
        maintainers = maintainers.data['maintainers']

        remove = request.GET.get('rem_maint')
        if remove is not None:
            resp = boss_maint.delete(request, group_name, remove)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/group/' + group_name)

        data = {}
        for member in members:
            data[member] = 'member'
            if member in maintainers:
                data[member] += '+maintainer'
        for maintainer in maintainers:
            if maintainer not in members:
                data[maintainer] = 'maintainer'


        args = {
            'group_name': group_name,
            'rows': data.items(),
            'members': members,
            'maintainers': maintainers,
            'form': GroupMemberForm(),
        }
        return HttpResponse(render_to_string('group.html', args, RequestContext(request)))

    def post(self, request, group_name):
        form = GroupMemberForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']

            if 'member' in role:
                boss_memb = BossGroupMember()
                boss_memb.request = request
                resp = boss_memb.post(request, group_name, user)
                if resp.status_code != 204:
                    return resp

            if 'maintainer' in role:
                boss_maint = BossGroupMaintainer()
                boss_maint.request = request
                resp = boss_maint.post(request, group_name, user)
                if resp.status_code !=204:
                    return resp

            return HttpResponseRedirect('/v0.7/mgmt/group/' + group_name)

class CollectionForm(forms.Form):
    collection = forms.CharField()
    description = forms.CharField(required=False)

class CoordinateFrameForm(forms.Form):
    name = forms.CharField(label="Coordinate Frame")
    description = forms.CharField(required=False)

    x_start = forms.IntegerField()
    x_stop = forms.IntegerField()

    y_start = forms.IntegerField()
    y_stop = forms.IntegerField()

    z_start = forms.IntegerField()
    z_stop = forms.IntegerField()

    x_voxel_size = forms.IntegerField()
    y_voxel_size = forms.IntegerField()
    z_voxel_size = forms.IntegerField()
    voxel_unit = forms.ChoiceField(choices=[(c,c) for c in ['', 
                                                            'nanometers', 
                                                            'micrometers', 
                                                            'millimeters', 
                                                            'centimeters']])

    time_step = forms.IntegerField(required=False)
    time_step_unit = forms.ChoiceField(required=False,
                                       choices=[(c,c) for c in ['', 
                                                                'nanoseconds', 
                                                                'microseconds', 
                                                                'milliseconds', 
                                                                'seconds']]) 

class Resources(LoginRequiredMixin, View):
    def get(self, request):
        delete = request.GET.get('del_col')
        if delete:
            boss = CollectionDetail()
            boss.request = request
            resp = boss.delete(request, delete)
            if resp.status_code != 204:
                return resp
            return HttpResponseRedirect('/v0.7/mgmt/resources/')

        delete = request.GET.get('del_coord')
        if delete:
            boss = CoordinateFrameDetail()
            boss.request = request
            resp = boss.delete(request, delete)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/resources/')

        boss = CollectionList()
        boss.request = request
        collections = boss.get(request)
        if collections.status_code != 200:
            return collections

        boss = CoordinateFrameList()
        boss.request = request
        coords = boss.get(request)
        if coords.status_code != 200:
            return coords

        args = {
            'collections': collections.data['collections'],
            'coords': coords.data['coords'],
            'col_form': CollectionForm(),
            'coord_form': CoordinateFrameForm(),
        }
        return HttpResponse(render_to_string('collections.html', args, RequestContext(request)))

    def post(self, request):
        action = request.GET.get('action') # URL parameter

        if action == 'col':
            form = CollectionForm(request.POST)
            if form.is_valid():
                collection = form.cleaned_data['collection']
                description = form.cleaned_data['description']

                boss = CollectionDetail()
                boss.request = request # needed for check_role() to work
                boss.request.data = {'description': description} # simulate the DRF request object
                resp = boss.post(request, collection)
                if resp.status_code != 201:
                    return resp # should reformat to a webpage

                return HttpResponseRedirect('/v0.7/mgmt/resources/')
        elif action == 'coord':
            form = CoordinateFrameForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                coord_name = data['coordinate_frame']
                del data['coordinate_frame']

                boss = CoordinateFrameDetail()
                boss.request = request
                boss.request.data = data
                resp = boss.post(request, coord_name)
                if resp.status_code != 201:
                    return resp

                return HttpResponseRedirect('/v0.7/mgmt/resources/')

class ExperimentForm(forms.Form):
    name = forms.CharField(label="Experiment")
    description = forms.CharField(required=False)

    coord_frame = forms.CharField() # DP TODO: make a drop down with valid coord frame names
    num_hierarchy_levels = forms.IntegerField()
    hierarchy_method = forms.ChoiceField(choices=[(c,c) for c in ['', 'near_iso', 'iso', 'slice']])
    num_time_samples = forms.IntegerField()

class MetaForm(forms.Form):
    key = forms.CharField()
    value = forms.CharField(widget=forms.Textarea)

class Collection(LoginRequiredMixin, View):
    def get(self, request, collection_name):
        # Load data from different models
        boss = CollectionDetail()
        boss.request = request
        collection = boss.get(request, collection_name)
        if collection.status_code != 200:
            return collection
        collection = collection.data

        boss = BossMeta()
        boss.request = request
        boss.request.version = 'v0.7' # DP HACK: reference config file
        boss.request.query_params = {}
        metas = boss.get(request, collection_name)
        if metas.status_code != 200:
            return metas
        metas = metas.data['keys']

        # Handle deleting items from data models
        remove = request.GET.get('rem_exp')
        if remove is not None:
            boss = ExperimentDetail()
            boss.request = request
            resp = boss.delete(request, collection_name, remove)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/collection/' + collection_name)

        remove = request.GET.get('rem_meta')
        if remove is not None:
            boss = BossMeta()
            boss.request = request
            boss.request.version = 'v0.7' # DP HACK: reference config file
            boss.request.query_params = {'key': remove}
            resp = boss.delete(request, collection_name)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/collection/' + collection_name)

        args = {
            'collection_name': collection_name,
            'collection': collection,
            'metas': metas,
            'exp_form': ExperimentForm(),
            'meta_form': MetaForm(),
        }
        return HttpResponse(render_to_string('collection.html', args, RequestContext(request)))

    def post(self, request, collection_name):
        action = request.GET.get('action') # URL parameter

        if action == 'exp':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                experiment_name = data['name']

                boss = ExperimentDetail()
                boss.request = request
                boss.request.data = data
                resp = boss.post(request, collection_name, experiment_name)
                if resp.status_code != 201:
                    return resp

                return HttpResponseRedirect('/v0.7/mgmt/collection/' + collection_name)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                params = form.cleaned_data.copy()

                boss = BossMeta()
                boss.request = request
                boss.request.version = 'v0.7' # DP HACK: reference config file
                boss.request.query_params = params
                resp = boss.post(request, collection_name)
                if resp.status_code != 201:
                    return resp

                return HttpResponseRedirect('/v0.7/mgmt/collection/' + collection_name)
            raise Exception(form.errors)

class Meta(LoginRequiredMixin, View):
    def get(self, request, collection, experiment=None, channel=None):
        boss = BossMeta()
        boss.request = request # needed for check_role() to work
        boss.request.version = 'v0.7' # DP HACK: reference config file
        boss.request.query_params = request.GET

        meta = boss.get(request, collection, experiment, channel)

        if meta.status_code != 200:
            return meta # should reformat to a webpage

        if channel is not None:
            category = "Channel"
            category_name = channel
        elif experiment is not None:
            category = "Experiment"
            category_name = experiment
        else:
            category = "Collection"
            category_name = collection


        args = {
            'category': category,
            'category_name': category_name,
            'key': meta.data['key'],
            'value': meta.data['value'],
        }
        return HttpResponse(render_to_string('meta.html', args, RequestContext(request)))

class CoordinateFrame(LoginRequiredMixin, View):
    def get(self, request, coord_name):
        boss = CoordinateFrameDetail()
        boss.request = request # needed for check_role() to work

        coord = boss.get(request, coord_name)

        if coord.status_code != 200:
            return coord # should reformat to a webpage

        args = {
            'coord_name': coord_name,
            'form': CoordinateFrameForm(coord.data)
        }
        return HttpResponse(render_to_string('coordinate_frame.html', args, RequestContext(request)))

class ChannelForm(forms.Form):
    name = forms.CharField(label="Channel")
    description = forms.CharField(required=False)

    type = forms.ChoiceField(choices=[(c,c) for c in ['', 'image', 'annotation']])
    datatype = forms.ChoiceField(choices=[(c,c) for c in ['', 'uint8', 'uint16', 'uint32', 'uint64']])

    base_resolution = forms.IntegerField(required=False)
    default_time_step = forms.IntegerField(required=False)
    source = forms.CharField(required=False) # DP TODO: create custom field type that splits on '.'
    related = forms.CharField(required=False)

class Experiment(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name):
        # Load data from different models
        boss = ExperimentDetail()
        boss.request = request
        experiment = boss.get(request, collection_name, experiment_name)
        if experiment.status_code != 200:
            return experiment
        experiment = experiment.data

        boss = ChannelList()
        boss.request = request
        channels = boss.get(request, collection_name, experiment_name)
        if channels.status_code != 200:
            return channels
        channels = channels.data['channels']

        boss = BossMeta()
        boss.request = request
        boss.request.version = 'v0.7' # DP HACK: reference config file
        boss.request.query_params = {}
        metas = boss.get(request, collection_name, experiment_name)
        if metas.status_code != 200:
            return metas
        metas = metas.data['keys']

        # DP TODO: Move to the first thing in the function
        # Handle deleting items from data models
        remove = request.GET.get('rem_chan')
        if remove is not None:
            boss = ChannelDetail()
            boss.request = request
            resp = boss.delete(request, collection_name, experiment_name, remove)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/resources/{}/{}'.format(collection_name, experiment_name))

        remove = request.GET.get('rem_meta')
        if remove is not None:
            boss = BossMeta()
            boss.request = request
            boss.request.version = 'v0.7' # DP HACK: reference config file
            boss.request.query_params = {'key': remove}
            resp = boss.delete(request, collection_name, experiment_name)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/resources/{}/{}'.format(collection_name, experiment_name))

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'exp_form': ExperimentForm(experiment),
            'channels': channels,
            'metas': metas,
            'chan_form': ChannelForm(),
            'meta_form': MetaForm(),
        }
        return HttpResponse(render_to_string('experiment.html', args, RequestContext(request)))

    def post(self, request, collection_name, experiment_name):
        action = request.GET.get('action') # URL parameter

        if action == 'chan':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                channel_name = data['name']
                if 'source' in data:
                    data['source'] = data['source'].split(',')
                if 'related' in data:
                    data['related'] = data['related'].split(',')

                boss = ChannelDetail()
                boss.request = request
                boss.request.data = data
                resp = boss.post(request, collection_name, experiment_name, channel_name)
                if resp.status_code != 201:
                    return resp

                return HttpResponseRedirect('/v0.7/mgmt/resources/{}/{}'.format(collection_name, experiment_name))
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                params = form.cleaned_data.copy()

                boss = BossMeta()
                boss.request = request
                boss.request.version = 'v0.7' # DP HACK: reference config file
                boss.request.query_params = params
                resp = boss.post(request, collection_name, experiment_name)
                if resp.status_code != 201:
                    return resp

                return HttpResponseRedirect('/v0.7/mgmt/resources/{}/{}'.format(collection_name, experiment_name))

class Channel(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, channel_name):
        remove = request.GET.get('rem_meta')
        if remove is not None:
            boss = BossMeta()
            boss.request = request
            boss.request.version = 'v0.7' # DP HACK: reference config file
            boss.request.query_params = {'key': remove}
            resp = boss.delete(request, collection_name, experiment_name, channel_name)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/resources/{}/{}/{}'.format(collection_name, experiment_name, channel_name))

        boss = ChannelDetail()
        boss.request = request # needed for check_role() to work
        channel = boss.get(request, collection_name, experiment_name, channel_name)
        if channel.status_code != 200:
            return channel # should reformat to a webpage

        boss = BossMeta()
        boss.request = request
        boss.request.version = 'v0.7' # DP HACK: reference config file
        boss.request.query_params = {}
        metas = boss.get(request, collection_name, experiment_name, channel_name)
        if metas.status_code != 200:
            return metas
        metas = metas.data['keys']

        args = {
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'channel_name': channel_name,
            'form': ChannelForm(channel.data),
            'metas': metas,
            'meta_form': MetaForm(),
        }
        return HttpResponse(render_to_string('channel.html', args, RequestContext(request)))

    def post(self, request, collection_name, experiment_name, channel_name):
        action = request.GET.get('action') # URL parameter

        if action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                params = form.cleaned_data.copy()

                boss = BossMeta()
                boss.request = request
                boss.request.version = 'v0.7' # DP HACK: reference config file
                boss.request.query_params = params
                resp = boss.post(request, collection_name, experiment_name, channel_name)
                if resp.status_code != 201:
                    return resp

                return HttpResponseRedirect('/v0.7/mgmt/resources/{}/{}/{}'.format(collection_name, experiment_name, channel_name))

