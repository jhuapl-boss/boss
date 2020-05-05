from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from bosscore.privileges import BossPrivilegeManager, check_role
from bosscore.error import BossError

from .forms import UserForm, RoleForm, GroupForm, GroupMemberForm
from .forms import CollectionForm, ExperimentForm, ChannelForm
from .forms import CoordinateFrameForm, MetaForm
from .forms import ResourcePermissionsForm, GroupPermissionsForm

from . import api
from . import utils
from .models import SystemNotice, BlogPost
import datetime

# import as to deconflict with our Token class
from rest_framework.authtoken.models import Token as TokenModel


# DP NOTE: If a form fails validation in the post() method, then
#          the populated form is passed to the get() method to
#          generate the same submission page, but with a form
#          that displays the validation errors

def redirect_frag(page, *args, frag=None):
    url = reverse(page, args=[*args])
    if frag:
        url += '#' + frag
    return redirect(url)


def get_roles(request):
    return list(BossPrivilegeManager(request.user).roles)


class Home(LoginRequiredMixin, View):
    def get(self, request):
        # Get System Notices
        now_datetime = datetime.datetime.now()
        notices = SystemNotice.objects.filter(show_on__lte=now_datetime, hide_on__gte=now_datetime)
        notice_data = []
        for n in notices:
            notice_data.append({"class": n.type,
                                "title": n.heading,
                                "msg": n.message})

        blogs = BlogPost.objects.filter(post_on__lte=now_datetime).order_by('-post_on')[:3]
        blog_data = []
        for b in blogs:
            blog_data.append({"title": b.title,
                              "msg": b.message,
                              "date": b.post_on})

        args = {
            'user_roles': get_roles(request),
            'alerts': notice_data,
            'blog_posts': blog_data
        }
        return HttpResponse(render_to_string('home.html', args, request=request))


class Users(LoginRequiredMixin, View):

    def get(self, request, user_form=None):
        page_error = None
        delete = request.GET.get('delete')
        if delete:
            err = api.del_user(request, delete)
            if err:
                page_error = err
            else:
                return redirect('mgmt:users')

        users, err = api.get_users(request)  # search query parameter will be automatically passed
        if err:
            return err

        user_data = []
        for user in users:
            if user['username'] == "bossadmin":
                # Skip bossadmin so you can't mess with the bossadmin roles easily.
                continue

            if "firstName" in user and "lastName" in user:
                name = "{} {}".format(user['firstName'], user['lastName'])
            else:
                name = " - "
            if "email" in user:
                email = user['email']
            else:
                email = " - "

            details_button = '<a type="button" class="btn btn-default btn-sm action-button" href="user/{}"><span class="glyphicon glyphicon-pencil" aria-hidden="true"></span> Manage Roles</a>'.format(user['username'])
            delete_button = '<a type="button" class="btn btn-danger btn-sm action-button" href="?delete={}"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Delete User</a>'.format(user['username'])
            user_data.append({"username": user['username'],
                              "name": name,
                              "email": email,
                              "actions": "{} {}".format(details_button, delete_button)})

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'user_data': user_data,
            'user_form': user_form if user_form else UserForm(),
            'user_error': "error" if user_form else "",
        }
        return HttpResponse(render_to_string('users.html', args, request=request))

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data.copy()
            username = data['username']
            del data['username']
            del data['verify_password']
            err = api.add_user(request, username, data)
            if err:
                form.add_error(None, err)
            else:
                return redirect('mgmt:users')

            #
            #try:
            #    err = api.add_user(request, username, data)
            #    if err:
            #        form.add_error(None, err)
            #    else:
            #        return redirect('mgmt:users')
            #except Exception as err:
            #    form.add_error(None, err)
        return self.get(request, user_form=form)


class User(LoginRequiredMixin, View):

    def get(self, request, username, role_form=None):
        page_error = None
        remove = request.GET.get('remove')
        if remove is not None:
            err = api.del_role(request, username, remove)
            if err:
                page_error = err
            else:
                return redirect_frag('mgmt:user', username, frag='Roles')

        user, err = api.get_user(request, username)
        if err:
            return err

        rows = []
        rows.append(('Username', user['username']))
        rows.append(('First Name', user.get('firstName', '')))
        rows.append(('Last Name', user.get('lastName', '')))
        rows.append(('Email', user.get('email', '')))

        roles = user['realmRoles']
        #headers = ["Roles", "Actions"]
        #fmt = lambda r: (r, '<a href="?remove={}#Role">Remove Role</a>'.format(r))
        #roles_args = utils.make_pagination(request, headers, roles, fmt, frag='#Roles')

        role_data = []
        for role in roles:
            role_data.append({"role": role,
                              "actions": '<a type="button" class="btn btn-danger btn-sm action-button" href="?remove={}"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Remove Role</a>'.format(role)})

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'username': username,
            'rows': rows,
            'role_data': role_data,
            'role_form': role_form if role_form else RoleForm(),
            'role_error': "error" if role_form else "",
        }
        return HttpResponse(render_to_string('user.html', args, request=request))

    def post(self, request, username):
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']

            err = api.add_role(request, username, role)
            if err:
                form.add_error(None, err)
            else:
                return redirect_frag('mgmt:user', username, frag='Roles')
        return self.get(request, username, role_form=form)


class Token(LoginRequiredMixin, View):
    def get(self, request):
        try:
            token = TokenModel.objects.get(user=request.user)
            button = "Revoke Token"
        except:
            token = None
            button = "Generate Token"

        args = {
            'user_roles': get_roles(request),
            'username': request.user,
            'token': token,
            'button': button,
        }
        return HttpResponse(render_to_string('token.html', args, request=request))

    def post(self, request):
        try:
            token = TokenModel.objects.get(user=request.user)
            token.delete()
        except:
            token = TokenModel.objects.create(user=request.user)

        return redirect('mgmt:token')


class Groups(LoginRequiredMixin, View):
    def get(self, request, group_form=None):
        page_error = None

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'group_form': group_form if group_form else GroupForm(),
            'group_error': "error" if group_form else ""
        }
        return HttpResponse(render_to_string('groups.html', args, request=request))

    def post(self, request):
        form = GroupForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['group_name']

            err = api.add_group(request, group_name)
            if err:
                form.add_error(None, err)
            else:
                return redirect('mgmt:groups')
        return self.get(request, group_form=form)


class Group(LoginRequiredMixin, View):
    def get(self, request, group_name, memb_form=None, perms_form=None):
        page_error = None
        remove = request.GET.get('rem_memb')
        if remove is not None:
            err = api.del_member(request, group_name, remove)
            if err:
                page_error = err
            else:
                return redirect_frag('mgmt:group', group_name, frag='Users')

        remove = request.GET.get('rem_maint')
        if remove is not None:
            err = api.del_maintainer(request, group_name, remove)
            if err:
                page_error = err
            else:
                return redirect_frag('mgmt:group', group_name, frag='Users')

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, *remove.split('/'), group=group_name)
            if err:
                page_error = err
            else:
                return redirect_frag('mgmt:group', group_name, frag='Permissions')

        group, err = api.get_group(request, group_name)
        if err:
            return err

        members, err = api.get_members(request, group_name)
        if err:
            return err

        maintainers, err = api.get_maintainers(request, group_name)
        if err:
            return err

        perms, err = utils.get_perms(request, group=group_name)
        print(perms)
        if err:
            return err

        users = list(members)
        for user in maintainers:
            if user not in users:
                users.append(user)

        group_member_data = []
        for user in users:
            perms_set = []
            actions_set = []
            if user in members:
                perms_set.append('member')
                actions_set.append('<a type="button" class="btn btn-danger btn-sm action-button" href="?rem_memb={}">Remove as Member</a>'.format(user))
            if user in maintainers:
                perms_set.append('maintainer')
                actions_set.append('<a type="button" class="btn btn-danger btn-sm action-button" href="?rem_maint={}">Remove as Maintainer</a>'.format(user))
            perms_set = '+'.join(perms_set)
            actions_set = ' '.join(actions_set)
            group_member_data.append({"user": user,
                                      "permissions": perms_set,
                                      "actions": actions_set})

        for perm in perms:
            perm["actions"] = '<a type="button" class="btn btn-danger btn-sm action-button" href="?rem_perms={}">Remove Permission Set</a>'.format(perm["group"])
            perm["resource"] = perm["group"]

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'group_name': group_name,
            'group': group,
            'users': users,
            'members': members,
            'maintainers': maintainers,
            'group_member_data': group_member_data,
            'perms': perms,
            'memb_form': memb_form if memb_form else GroupMemberForm(),
            'memb_error': "error" if memb_form else "",
            'perms_form': perms_form if perms_form else GroupPermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('group.html', args, request=request))

    def post(self, request, group_name):
        action = request.GET.get('action')  # URL parameter
        if action == 'memb':
            form = GroupMemberForm(request.POST)
            if form.is_valid():
                user = form.cleaned_data['user']
                role = form.cleaned_data['role']

                memb_err = None
                if 'member' in role:
                    memb_err = api.add_member(request, group_name, user)
                    if memb_err:
                        form.add_error(None, memb_err)

                maint_err = None
                if 'maintainer' in role:
                    maint_err = api.add_maintainer(request, group_name, user)
                    if maint_err:
                        form.add_error(None, maint_err)

                if not memb_err and not maint_err:
                    return redirect('mgmt:group', group_name)

            return self.get(request, group_name, memb_form=form)
        elif action == 'perms':
            form = GroupPermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, group=group_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:group', group_name)
            return self.get(request, group_name, perms_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")


class Resources(LoginRequiredMixin, View):
    def get(self, request, col_form=None, coord_form=None):
        page_error = None

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'col_form': col_form if col_form else CollectionForm(prefix="col"),
            'col_error': "error" if col_form else "",
            'coord_form': coord_form if coord_form else CoordinateFrameForm(prefix="coord", initial={"x_start": 0,
                                                                                                     "y_start": 0,
                                                                                                     "z_start": 0}),
            'coord_error': "error" if coord_form else "",
        }
        return HttpResponse(render_to_string('collections.html', args, request=request))

    def post(self, request):
        print(request.POST)
        if 'col-name' in request.POST:
            form = CollectionForm(request.POST, prefix="col")
            if form.is_valid():
                data = form.cleaned_data.copy()
                collection = data['name']
                print(collection)

                err = api.add_collection(request, collection, data)
                if err:
                    print(err)
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:resources')
            return self.get(request, col_form=form)
        elif 'coord-name' in request.POST:
            form = CoordinateFrameForm(request.POST, prefix="coord")
            if form.is_valid():
                data = form.cleaned_data.copy()
                coord_name = data['name']

                err = api.add_coord(request, coord_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:resources')
            return self.get(request, coord_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")


class CoordinateFrame(LoginRequiredMixin, View):
    def get(self, request, coord_name, coord_form=None):
        if not coord_form:
            coord, err = api.get_coord(request, coord_name)
            if err:
                return err
            coord_form = CoordinateFrameForm(coord).is_update()
            coord_error = ""
        else:
            coord_form.is_update()
            coord_error = "error"

        args = {
            'user_roles': get_roles(request),
            'coord_name': coord_name,
            'coord_form': coord_form,
            'coord_error': coord_error,
        }
        return HttpResponse(render_to_string('coordinate_frame.html', args, request=request))

    @check_role("resource-manager")
    def post(self, request, coord_name):
        form = CoordinateFrameForm(request.POST)
        if form.is_valid():
            data = form.cleaned_update_data

            err = api.up_coord(request, coord_name, data)
            if err:
                form.add_error(None, err)
            else:
                return redirect('mgmt:coord', data['name'])
        return self.get(request, coord_name, coord_form=form)


class Collection(LoginRequiredMixin, View):
    def get(self, request, collection_name, col_form=None, exp_form=None, meta_form=None, perms_form=None):
        page_error = None

        # Use a GET request to the mgmt console to convert the UI representation of permissions into actual API calls
        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, group=remove)
            if err:
                page_error = err
            else:
                return redirect('mgmt:collection', collection_name)

        collection, err = api.get_collection(request, collection_name)
        if err:
            return err

        if not col_form:
            col_form = CollectionForm(collection)
            col_error = ""
        else:
            col_error = "error"

        metas, err = api.get_meta_keys(request, collection_name)
        if err:
            return err

        perms, err = utils.get_perms(request, collection_name)
        if err:
            return err

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'collection_name': collection_name,
            'collection': collection,
            'metas': metas,
            'perms': perms,
            'col_form': col_form,
            'col_error': col_error,
            'exp_form': exp_form if exp_form else ExperimentForm(initial={"num_time_samples": 1,
                                                                          "hierarchy_method": "near_iso",
                                                                          "num_hierarchy_levels": 7}),
            'exp_error': "error" if exp_form else "",
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
            'perms_form': perms_form if perms_form else ResourcePermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('collection.html', args, request=request))

    def post(self, request, collection_name):
        action = request.GET.get('action')  # URL parameter
        if action == 'exp':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                experiment_name = data['name']

                err = api.add_experiment(request, collection_name, experiment_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:collection', collection_name)
            return self.get(request, collection_name, exp_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:collection', collection_name)
            return self.get(request, collection_name, meta_form=form)
        elif action == 'perms':
            print(request.POST)
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:collection', collection_name)
            return self.get(request, collection_name, perms_form=form)
        elif action == 'update':
            form = CollectionForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()

                err = api.up_collection(request, collection_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:collection', data['name'])
            return self.get(request, collection_name, col_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")


class Experiment(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, exp_form=None, chan_form=None, meta_form=None,
            perms_form=None):
        page_error = None

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, experiment_name, group=remove)
            if err:
                page_error = err
            else:
                return redirect('mgmt:experiment', collection_name, experiment_name)

        experiment, err = api.get_experiment(request, collection_name, experiment_name)
        if err:
            return err

        if not exp_form:
            exp_form = ExperimentForm(experiment).is_update()
            exp_error = ""
        else:
            exp_form.is_update()
            exp_error = "error"

        metas, err = api.get_meta_keys(request, collection_name, experiment_name)
        if err:
            return err

        perms, err = utils.get_perms(request, collection_name, experiment_name)
        if err:
            return err

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'experiment': experiment,
            'metas': metas,
            'perms': perms,
            'exp_form': exp_form,
            'exp_error': exp_error,
            'chan_form': chan_form if chan_form else ChannelForm(initial={"base_resolution": 0,
                                                                          "default_time_sample": 0}),
            'chan_error': "error" if chan_form else "",
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
            'perms_form': perms_form if perms_form else ResourcePermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('experiment.html', args, request=request))

    def post(self, request, collection_name, experiment_name):
        action = request.GET.get('action')  # URL parameter

        if action == 'chan':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data.copy()
                channel_name = data['name']

                err = api.add_channel(request, collection_name, experiment_name, channel_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:experiment', collection_name, experiment_name)
            return self.get(request, collection_name, experiment_name, chan_form=form)
        elif action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:experiment', collection_name, experiment_name)
            return self.get(request, collection_name, experiment_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name, experiment_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:experiment', collection_name, experiment_name)
            return self.get(request, collection_name, experiment_name, perms_form=form)
        elif action == 'update':
            form = ExperimentForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                err = api.up_experiment(request, collection_name, experiment_name, data)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:experiment', collection_name, data['name'])
            return self.get(request, collection_name, experiment_name, exp_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")


class Channel(LoginRequiredMixin, View):
    def get(self, request, collection_name, experiment_name, channel_name, chan_form=None, meta_form=None,
            perms_form=None):
        page_error = None

        remove = request.GET.get('rem_perms')
        if remove is not None:
            err = api.del_perms(request, collection_name, experiment_name, channel_name, group=remove)
            if err:
                page_error = err
            else:
                return redirect('mgmt:channel', collection_name, experiment_name, channel_name)

        channel, err = api.get_channel(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        if not chan_form:
            chan_form = ChannelForm(channel).is_update()
            chan_error = ""
        else:
            chan_form.is_update()
            chan_error = "error"

        metas, err = api.get_meta_keys(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        perms, err = utils.get_perms(request, collection_name, experiment_name, channel_name)
        if err:
            return err

        args = {
            'user_roles': get_roles(request),
            'page_error': page_error,
            'collection_name': collection_name,
            'experiment_name': experiment_name,
            'channel_name': channel_name,
            'channel': channel,
            'metas': metas,
            'perms': perms,
            'chan_form': chan_form,
            'chan_error': chan_error,
            'meta_form': meta_form if meta_form else MetaForm(),
            'meta_error': "error" if meta_form else "",
            'perms_form': perms_form if perms_form else ResourcePermissionsForm(),
            'perms_error': "error" if perms_form else "",
        }
        return HttpResponse(render_to_string('channel.html', args, request=request))

    def post(self, request, collection_name, experiment_name, channel_name):
        action = request.GET.get('action')  # URL parameter

        if action == 'meta':
            form = MetaForm(request.POST)
            if form.is_valid():
                key = form.cleaned_data['key']
                value = form.cleaned_data['value']

                err = api.add_meta(request, key, value, collection_name, experiment_name, channel_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:channel', collection_name, experiment_name, channel_name)
            return self.get(request, collection_name, experiment_name, channel_name, meta_form=form)
        elif action == 'perms':
            form = ResourcePermissionsForm(request.POST)
            if form.is_valid():
                err = utils.set_perms(request, form, collection_name, experiment_name, channel_name)
                if err:
                    form.add_error(None, err)
                else:
                    return redirect('mgmt:channel', collection_name, experiment_name, channel_name)
            return self.get(request, collection_name, experiment_name, channel_name, perms_form=form)
        elif action == 'update':
            form = ChannelForm(request.POST)
            if form.is_valid():
                data = form.cleaned_update_data

                # DMK - Boss request throws a BossError if the related channels don't exist
                try:
                    err = api.up_channel(request, collection_name, experiment_name, channel_name, data)

                    if err:
                        form.add_error(None, err)
                    else:
                        return redirect('mgmt:channel', collection_name, experiment_name, data['name'])

                except BossError as err:
                    form.add_error(None, err.message)


            return self.get(request, collection_name, experiment_name, channel_name, chan_form=form)
        else:
            return HttpResponse(status=400, reason="Unknown post action")


class Meta(LoginRequiredMixin, View):
    def get(self, request, collection, experiment=None, channel=None, meta_form=None):
        if not meta_form:
            key = request.GET['key']
            meta, err = api.get_meta(request, key, collection, experiment, channel)
            if err:
                return err
            meta_form = MetaForm(meta).is_update()
            meta_error = ""
        else:
            meta_form.is_update()
            meta_error = "error"

        if channel is not None:
            category = "Channel"
            category_name = channel
            back_url = reverse('mgmt:channel', args=[collection, experiment, channel])
        elif experiment is not None:
            category = "Experiment"
            category_name = experiment
            back_url = reverse('mgmt:experiment', args=[collection, experiment])
        else:
            category = "Collection"
            category_name = collection
            back_url = reverse('mgmt:collection', args=[collection])

        args = {
            'user_roles': get_roles(request),
            'category': category,
            'category_name': category_name,
            'meta_form': meta_form,
            'meta_error': meta_error,
            'back_url': back_url
        }
        return HttpResponse(render_to_string('meta.html', args, request=request))

    @check_role("resource-manager")
    def post(self, request, collection, experiment=None, channel=None):
        form = MetaForm(request.POST)
        if form.is_valid():
            key = form.cleaned_data['key']
            value = form.cleaned_data['value']

            if channel is not None:
                back_url = reverse('mgmt:channel', args=[collection, experiment, channel])
            elif experiment is not None:
                back_url = reverse('mgmt:experiment', args=[collection, experiment])
            else:
                back_url = reverse('mgmt:collection', args=[collection])

            err = api.up_meta(request, key, value, collection, experiment, channel)
            if err:
                form.add_error(None, err)
            else:
                return HttpResponseRedirect(back_url)
        return self.get(request, collection, experiment, channel, meta_form=form)


class IngestJob(LoginRequiredMixin, View):
    def get(self, request, ingest_job_id=None):
        args = {'user_roles': get_roles(request),
                'id':ingest_job_id}

        if not ingest_job_id:
            # This is just the main ingest job listing
            return HttpResponse(render_to_string('ingest_jobs.html', args, request=request))

        else:
            # This is a single ingest job
            return HttpResponse(render_to_string('ingest_job.html', args, request=request))

