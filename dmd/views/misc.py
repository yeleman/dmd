#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.static import serve

from dmd.models.Partners import Partner

logger = logging.getLogger(__name__)


def home(request, *args, **kwargs):
    context = {'page': 'home'}

    return render(request,
                  kwargs.get('template_name', 'home.html'),
                  context)


def user_profile(request, username, *args, **kwargs):
    context = {'page': 'profile'}

    partner = Partner.get_or_none(username)
    if partner is None:
        raise Http404(_("Unable to find Partner with username `{username}`")
                      .format(username=username))

    context.update({'partner': partner})

    return render(request,
                  kwargs.get('template_name', 'public_profile.html'),
                  context)


class ChangePasswordForm(forms.Form):

    old_password = forms.CharField(max_length=255, widget=forms.PasswordInput,
                                   label=ugettext_lazy("Old Password"))
    new_password = forms.CharField(max_length=255, widget=forms.PasswordInput,
                                   label=ugettext_lazy("New Password"))

    def __init__(self, *args, **kwargs):
        self.partner = kwargs.pop('partner')
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        op = self.cleaned_data.get('old_password')
        if not self.partner.user.check_password(op):
            raise forms.ValidationError(
                _("Old password for `{partner}` is invalid")
                .format(partner=self.partner),
                code='invalid',
                params={'partner': self.partner})
        return op


@login_required
def user_change_password(request, *args, **kwargs):
    context = {'page': 'users'}
    partner = request.user.partner

    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, partner=partner)
        if form.is_valid():
            with transaction.atomic():
                partner.user.set_password(
                    form.cleaned_data.get('new_password'))
                partner.user.save()

            messages.success(request,
                             _("Your password has been updated."))
            return redirect('users')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = ChangePasswordForm(partner=partner)

    context.update({
        'form': form,
        'partner': partner})

    return render(request,
                  kwargs.get('template_name', 'user_change_password.html'),
                  context)


@login_required
def serve_exported_files(request, fpath=None):
    if settings.SERVE_EXPORTED_FILES:
        return serve(request, fpath, settings.EXPORT_REPOSITORY, True)

    response = HttpResponse()
    response['Content-Type'] = ''
    response['X-Accel-Redirect'] = "{protected_url}/{fpath}".format(
        protected_url=settings.EXPORT_REPOSITORY_URL_PATH,
        fpath=fpath)
    return response
