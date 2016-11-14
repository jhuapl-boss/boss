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

class Collections(LoginRequiredMixin, View):
    def get(self, request):
        delete = request.GET.get('delete')
        if delete:
            boss = CollectionDetail()
            boss.request = request
            resp = boss.delete(request, delete)
            if resp.status_code != 204:
                return resp
            return HttpResponseRedirect('/v0.7/mgmt/collections/')

        boss = CollectionList()
        boss.request = request
        collections = boss.get(request)
        if collections.status_code != 200:
            return collections

        args = {
            'collections': collections.data['collections'],
            'form': CollectionForm(),
        }
        return HttpResponse(render_to_string('collections.html', args, RequestContext(request)))

    def post(self, request):
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

            return HttpResponseRedirect('/v0.7/mgmt/collections/')

class CoordinateFrameForm(forms.Form):
    coordinate_frame = forms.CharField()
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
    voxel_units = forms.ChoiceField(choices=[(c,c) for c in ['', 
                                                             'nanometers', 
                                                             'micrometers', 
                                                             'millimeters', 
                                                             'centimeters']])

    time_step = forms.IntegerField(required=False)
    time_step_units = forms.ChoiceField(required=False,
                                        choices=[(c,c) for c in ['', 
                                                                 'nanoseconds', 
                                                                 'microseconds', 
                                                                 'milliseconds', 
                                                                 'seconds']]) 

class ExperimentForm(forms.Form):
    experiment = forms.CharField()
    description = forms.CharField(required=False)

    coord_frame_name = forms.CharField() # DP TODO: make a drop down with valid coord frame names
    num_hierarchy_levels = forms.IntegerField()
    hierarchy_method = forms.ChoiceField(choices=[(c,c) for c in ['', 'near_iso', 'iso', 'slice']])
    max_time_sample = forms.IntegerField()

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

        boss = ExperimentList()
        boss.request = request
        experiments = boss.get(request, collection_name)
        if experiments.status_code != 200:
            return experiments
        experiments = experiments.data['experiments']

        boss = CoordinateFrameList()
        boss.request = request
        coords = boss.get(request, collection_name)
        if coords.status_code != 200:
            return coords
        coords = coords.data['coords']

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

        remove = request.GET.get('rem_coord')
        if remove is not None:
            boss = CoordinateFrameDetail()
            boss.request = request
            resp = boss.delete(request, collection_name, remove)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/collection/' + collection_name)

        remove = request.GET.get('rem_meta')
        if remove is not None:
            boss = BossMeta()
            boss.request = request
            boss.request.query_params = {'key': remove}
            resp = boss.delete(request, collection_name)
            if resp.status_code != 204:
                return resp # should reformt to a webpage
            return HttpResponseRedirect('/v0.7/mgmt/collection/' + collection_name)

        args = {
            'collection_name': collection_name,
            'collection': collection,
            'experiments': experiments,
            'coords': coords,
            'metas': metas,
            'exp_form': ExperimentForm(),
            'coord_form': CoordinateFrameForm(),
            'meta_form': MetaForm(),
        }
        return HttpResponse(render_to_string('collection.html', args, RequestContext(request)))

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
