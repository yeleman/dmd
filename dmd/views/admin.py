#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import copy
import os
import datetime

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from django import forms
from django.db import transaction
from django.forms.models import model_to_dict, fields_for_model
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from babel.numbers import format_decimal

from dmd.models.Partners import Partner, User, Organization
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.utils import (random_password,
                       send_new_account_email, send_reset_password_email)

logger = logging.getLogger(__name__)


@login_required
@user_passes_test(lambda u: u.is_staff)
def users_list(request, *args, **kwargs):
    context = {'page': 'users',
               'partners': Partner.objects.all()}

    return render(request,
                  kwargs.get('template_name', 'users.html'),
                  context)


class PartnerForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        _fields = ('first_name', 'last_name', 'username', 'email',
                   'is_staff', 'is_active')
        kwargs['initial'] = model_to_dict(instance.user, _fields) \
            if instance is not None else None
        super(PartnerForm, self).__init__(*args, **kwargs)

        pfields = copy.copy(self.fields)
        self.fields = fields_for_model(User, _fields)
        for k, v in pfields.items():
            self.fields.update({k: v})

        # limit and better display entities
        choices = [e.to_treed_tuple() for e in Entity.clean_tree(Entity.ZONE)]
        self.fields['upload_location'].choices = choices
        self.fields['validation_location'].choices = choices

        if instance:
            self.fields['username'].widget.attrs['readonly'] = True

        self.instanciated = instance is not None

    def clean_username(self):
        cu = self.cleaned_data.get('username')
        if self.instanciated:
            return cu
        cu = slugify(cu)
        if User.objects.filter(username=cu).count():
            raise forms.ValidationError(
                _("Username `{username}` is already taken")
                .format(username=cu),
                code='invalid',
                params={'username': cu})
        return cu

    class Meta:
        model = Partner
        exclude = ('user',)


@login_required
def user_add(request, *args, **kwargs):
    context = {'page': 'users'}

    if request.method == 'POST':
        form = PartnerForm(request.POST, instance=None)
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create(
                    username=form.cleaned_data.get('username'),
                    first_name=form.cleaned_data.get('first_name'),
                    last_name=form.cleaned_data.get('last_name'),
                    email=form.cleaned_data.get('email'),
                    is_active=form.cleaned_data.get('is_active'),
                    is_staff=form.cleaned_data.get('is_staff'),
                    is_superuser=form.cleaned_data.get('is_staff'))
                passwd = random_password(True)
                user.set_password(passwd)
                user.save()

                partner = Partner.objects.create(
                    user=user,
                    organization=form.cleaned_data.get('organization'),
                    can_upload=form.cleaned_data.get('can_upload'),
                    upload_location=form.cleaned_data.get('upload_location'),
                    can_validate=form.cleaned_data.get('can_validate'),
                    validation_location=form.cleaned_data.get(
                        'validation_location')
                    )

            messages.success(request,
                             _("New User account “{name}” created with "
                               "login `{username}` and password `{password}`")
                             .format(name=partner, username=partner.username,
                                     password=passwd))

            email_sent, x = send_new_account_email(
                partner=partner, password=passwd,
                creator=Partner.from_user(request.user))
            if email_sent:
                messages.info(request,
                              _("The password has been sent to {email}")
                              .format(email=partner.email))

            return redirect('users')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = PartnerForm()

    context.update({'form': form})
    return render(request,
                  kwargs.get('template_name', 'user_add.html'),
                  context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_edit(request, username, *args, **kwargs):
    context = {'page': 'users'}
    partner = Partner.get_or_none(username)

    if request.method == 'POST':
        form = PartnerForm(request.POST, instance=partner)
        if form.is_valid():
            with transaction.atomic():
                partner.user.first_name = form.cleaned_data.get('first_name')
                partner.user.last_name = form.cleaned_data.get('last_name')
                partner.user.email = form.cleaned_data.get('email')
                partner.user.is_active = form.cleaned_data.get('is_active')
                partner.user.is_staff = form.cleaned_data.get('is_staff')
                partner.user.is_superuser = \
                    form.cleaned_data.get('is_superuser')
                partner.user.save()

                partner.organization = form.cleaned_data.get('organization')
                partner.can_upload = form.cleaned_data.get('can_upload')
                partner.upload_location = \
                    form.cleaned_data.get('upload_location')
                partner.can_validate = form.cleaned_data.get('can_validate')
                partner.validation_location = \
                    form.cleaned_data.get('validation_location')
                partner.save()

            messages.success(request,
                             _("User account “{name}” has been updated.")
                             .format(name=partner))
            return redirect('users')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = PartnerForm(instance=partner)

    context.update({
        'form': form,
        'partner': partner})

    return render(request,
                  kwargs.get('template_name', 'user_edit.html'),
                  context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_passwd_reset(request, username, *args, **kwargs):
    partner = Partner.get_or_none(username)
    passwd = random_password(True)
    partner.user.set_password(passwd)
    partner.user.save()
    messages.success(request,
                     _("Password for User account “{name}” "
                       "(login `{username}`) has been reseted to `{password}`")
                     .format(name=partner, username=partner.username,
                             password=passwd))
    email_sent, x = send_reset_password_email(
        partner=partner, password=passwd,
        creator=Partner.from_user(request.user))
    if email_sent:
        messages.info(request,
                      _("The password has been sent to {email}")
                      .format(email=partner.email))

    return redirect('users')


class IndicatorForm(forms.ModelForm):

    class Meta:
        model = Indicator
        exclude = ('user',)


@login_required
@user_passes_test(lambda u: u.is_staff)
def indicator_add(request, *args, **kwargs):
    context = {'page': 'indicators'}

    if request.method == 'POST':
        form = IndicatorForm(request.POST, instance=None)
        if form.is_valid():
            with transaction.atomic():
                indicator = form.save()

            messages.success(request,
                             _("New Indicator “{name}” created with "
                               "number `{number}`")
                             .format(name=indicator.name,
                                     number=indicator.number))
            return redirect('indicators')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = IndicatorForm()

    context.update({'form': form})

    return render(request,
                  kwargs.get('template_name', 'indicator_add.html'),
                  context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def indicator_edit(request, slug, *args, **kwargs):
    context = {'page': 'indicators'}

    indicator = Indicator.get_or_none(slug)

    if request.method == 'POST':
        form = IndicatorForm(request.POST, instance=indicator)
        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request,
                             _("Indicator “{name}” has been updated.")
                             .format(name=indicator))
            return redirect('indicators')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = IndicatorForm(instance=indicator)

    context.update({
        'form': form,
        'indicator': indicator})

    return render(request,
                  kwargs.get('template_name', 'indicator_edit.html'),
                  context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def organizations_list(request, *args, **kwargs):
    context = {'page': 'organizations',
               'organizations': Organization.objects.all()}

    return render(request,
                  kwargs.get('template_name', 'organizations.html'),
                  context)


class OrganizationForm(forms.ModelForm):

    class Meta:
        model = Organization
        exclude = ('user',)


@login_required
@user_passes_test(lambda u: u.is_staff)
def organization_add(request, *args, **kwargs):
    context = {'page': 'organizations'}

    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=None)
        if form.is_valid():
            with transaction.atomic():
                organization = form.save()

            messages.success(request,
                             _("New organization “{name}” created with "
                               "slug `{slug}`")
                             .format(name=organization.name,
                                     slug=organization.slug))
            return redirect('organizations')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = OrganizationForm()

    context.update({'form': form})

    return render(request,
                  kwargs.get('template_name', 'organization_add.html'),
                  context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def organization_edit(request, slug, *args, **kwargs):
    context = {'page': 'organizations'}

    organization = Organization.get_or_none(slug)

    if request.method == 'POST':
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            with transaction.atomic():
                form.save()

            messages.success(request,
                             _("Organization “{name}” has been updated.")
                             .format(name=organization))
            return redirect('organizations')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = OrganizationForm(instance=organization)

    context.update({
        'form': form,
        'organization': organization})

    return render(request,
                  kwargs.get('template_name', 'organization_edit.html'),
                  context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def backups_list(request, *args, **kwargs):
    context = {'page': 'backups'}

    def dt4fn(fn):
        try:
            x = datetime.datetime(*[int(x)
                                  for x in fn.rsplit('.7z', 1)[0]
                                  .rsplit('_', 1)[1].split('-')])
            return x
        except:
            return datetime.datetime.today()

    def fsfor(fn):
        fs = os.path.getsize(os.path.join(settings.BACKUPS_REPOSITORY, fn))
        if fs // 1024:
            suffix = 'K'
            fs = fs / 1024
        if fs // 1024:
            suffix = 'M'
            fs = fs / 1024
        return "{size}{suffix}b".format(size=format_decimal(fs, "#,##0.#;-#"),
                                        suffix=suffix)

    context.update({'backups': sorted(
        [{'fname': fname,
          'hsize': fsfor(fname),
          'fpath': os.path.join(settings.BACKUPS_DIR_NAME, fname)}
         for fname in os.listdir(settings.BACKUPS_REPOSITORY)
         if fname.endswith('.7z')],
        key=dt4fn, reverse=True)})

    return render(request,
                  kwargs.get('template_name', 'backups.html'),
                  context)
