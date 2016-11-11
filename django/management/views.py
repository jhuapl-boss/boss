from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.template.loader import render_to_string
from django.template import RequestContext
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django import forms

from sso.views.views_user import BossUser, BossUserRole

# import as to deconflict with our Token class
from rest_framework.authtoken.models import Token as TokenModel

class Home(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse(render_to_string('base.html'))

class Users(LoginRequiredMixin, View):
    def get(self, request):
        user = {'username': 'bossadmin'} # DP TODO: build needed API
        args = {
            'users': [user],
        }
        return HttpResponse(render_to_string('users.html', args, RequestContext(request)))

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
