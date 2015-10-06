#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import tempfile
import json
import os
import copy

from py3compat import text_type
from django.http import JsonResponse, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django import forms
from django.db import transaction
from django.forms.models import model_to_dict, fields_for_model
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.views.static import serve

from dmd.models import Entity, DataRecord, Partner, MonthPeriod, User, Metadata
from dmd.xls_import import (read_xls, ExcelValueMissing,
                            ExcelValueError, IncorrectExcelFile)
from dmd.utils import random_password, import_path
from dmd.analysis import SECTIONS

logger = logging.getLogger(__name__)

STEP2_KEY = 'needs_entity_step2'
XLS_DATA_KEY = 'xls_data'


def lineage_data_for(entity):
    if entity is None:
        return []
    lad = entity.lineage_data
    return [lad.get(ts, "") if ts != entity.etype else entity.uuid
            for ts in Entity.lineage()]


def home(request, *args, **kwargs):
    context = {'page': 'home'}

    return render(request,
                  kwargs.get('template_name', 'home.html'),
                  context)


def handle_uploaded_file(f):
    """ stores temporary file as a real file for form upload """
    tfile = tempfile.NamedTemporaryFile(delete=False)
    for chunk in f.chunks():
        tfile.write(chunk)
    tfile.close()
    return tfile.name


class ExcelUploadForm(forms.Form):
    data_file = forms.FileField(label=ugettext_lazy("Report File"))


def create_records_from(request, xls_data, filepath=None):
    redir = False
    try:
        payload = DataRecord.batch_create(xls_data,
                                          request.user.partner)
    except Exception as e:
        logger.exception(e)
        messages.error(request, text_type(e))
    else:
        nb_created = sum([1 for v in payload.values()
                          if v.get('action') == 'created'])
        nb_updated = sum([1 for v in payload.values()
                          if v.get('action') == 'updated'])
        if nb_created or nb_updated:
            message = _("Congratulations! Your data has been recorded.")
            if nb_created:
                message += "\n" + _("{nb_created} records were created.")
            if nb_updated:
                message += "\n" + _("{nb_updated} records were updated.")
            messages.success(request, message.format(nb_created=nb_created,
                                                     nb_updated=nb_updated))
        else:
            messages.info(request, _("Thank You for submitting! "
                                     "No new data to record though."))
        redir = True
    finally:
        if filepath is not None:
            os.unlink(filepath)
    return redir


@login_required
def upload(request, template_name='upload.html'):

    context = {'page': 'upload'}

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            filepath = handle_uploaded_file(request.FILES['data_file'])

            try:
                xls_data = read_xls(filepath)
            except Exception as e:
                logger.exception(e)
                if isinstance(e, (IncorrectExcelFile,
                                  ExcelValueMissing,
                                  ExcelValueError)):
                    messages.error(request, text_type(e))
                else:
                    messages.error(
                        request, _("Unexpected Error while reading XLS file"))
                return redirect('upload')

            # entity couldn't be found. store xls data in session
            # and offer a choice of entities to choose from
            if xls_data['meta'].get('entity') is None:
                request.session[XLS_DATA_KEY] = xls_data
                logger.debug("Redirecting to step2")
                return redirect('upload_step2')

            if create_records_from(request, xls_data, filepath):
                return redirect('upload')
        else:
            # django form validation errors
            pass
    else:
        form = ExcelUploadForm()

    context.update({'form': form})

    return render(request, template_name, context)


class ASChooserForm(forms.Form):
    entity = forms.ChoiceField(label=Entity.AIRE, choices=[])

    def __init__(self, *args, **kwargs):
        children = kwargs.pop('children')

        super(ASChooserForm, self).__init__(*args, **kwargs)

        self.fields['entity'].choices = [child.to_tuple()
                                         for child in children]

    def clean_entity(self):
        euuid = self.cleaned_data.get('entity')
        entity = Entity.get_or_none(euuid)
        if entity is None or entity not in [
                e[1] for e in self.fields['entity'].choices]:
            raise forms.ValidationError(
                _("Invalid Entity `{uuid}`"),
                code='invalid',
                params={'uuid': euuid})
        return entity


@login_required
def upload_step2(request, template_name='upload_step2.html'):
    context = {'page': 'upload'}

    if XLS_DATA_KEY not in request.session.keys():
        messages.error(request, _("You have no active session. "
                                  "Please upload your file"))
        return redirect('upload')

    xls_data = request.session.get('xls_data', {})
    if not xls_data:
        messages.error(request, _("You session is invalid. "
                                  "Please upload your file"))
        return redirect('upload')

    children = xls_data.get('meta', {}).get('as_candidates', [])

    # update context
    meta = xls_data['meta']
    context.update({'parent': meta['zs_entity'],
                    'candidates': meta['as_candidates'],
                    'name': meta['as']})

    if request.method == 'POST':
        form = ASChooserForm(request.POST, children=children)
        if form.is_valid():
            # retrieve xls data from session
            xls_data = request.session.pop(XLS_DATA_KEY)
            xls_data['meta']['as_entity'] = form.cleaned_data.get('entity')
            xls_data['meta']['entity'] = xls_data['meta']['as_entity']

            if not xls_data:
                messages.error(request, _("You session is invalid. "
                                          "Please upload your file"))
                return redirect('upload')

            if create_records_from(request, xls_data):
                logger.debug("reports created")
                return redirect('upload')
        else:
            # django form validation errors
            logger.debug("django form errors")
            pass
    else:
        form = ASChooserForm(children=children)

    context.update({'form': form})
    return render(request, template_name, context)


def process_entity_filter(request, entity_uuid=None):

    root = Entity.objects.get(level=0)
    entity = Entity.get_or_none(entity_uuid) if entity_uuid else root

    if entity is None:
        raise Http404(request,
                      _("Unable to match entity `{uuid}`")
                      .format(uuid=entity_uuid))

    return {
        'blank_uuid': "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        'root': root,
        'entity': entity,
        'lineage_data': lineage_data_for(entity),
        'lineage': Entity.lineage,
        'children': root.get_children(),
    }


def process_period_filter(request, period_str=None, name='period'):
    if period_str:
        period = MonthPeriod.get_or_none(period_str)
        if period is None:
            raise Http404(request,
                          _("Unable to match period with `{period}`")
                          .format(period=period_str))
    else:
        period = MonthPeriod.current().previous()

    return {
        'periods': sorted([p.to_tuple() for p in MonthPeriod.all_till_now()],
                          reverse=True),
        name: period,
    }


@login_required
def raw_data(request, entity_uuid=None, period_str=None, *args, **kwargs):
    context = {'page': 'raw_data'}

    # handling entity
    context.update(process_entity_filter(request, entity_uuid))

    # handling period
    context.update(process_period_filter(request, period_str))

    context.update({
        'records': DataRecord.objects
                             .filter(entity=context['entity'],
                                     period=context['period'])
                             .order_by('indicator__number')
    })

    return render(request,
                  kwargs.get('template_name', 'raw_data.html'),
                  context)


@login_required
def data_export(request, *args, **kwargs):
    context = {'page': 'export'}

    export = Metadata.get_or_none('nb_records')
    if export is not None:
        context.update({
            'nb_records': int(export.value),
            'export_date': export.updated_on,
            'export_fname': settings.ALL_EXPORT_FNAME,
        })

    return render(request,
                  kwargs.get('template_name', 'export.html'),
                  context)


@login_required
def analysis(request, section_id='1',
             entity_uuid=None, perioda_str=None, periodb_str=None,
             *args, **kwargs):
    context = {'page': 'analysis_section1'}

    if section_id not in SECTIONS:
        raise Http404(_("Unknown section ID `{sid}`").format(sid=section_id))

    section = import_path('dmd.analysis.section{}'.format(section_id))

    # handling entity
    context.update(process_entity_filter(request, entity_uuid))

    # handling periods
    context.update(process_period_filter(request, perioda_str, 'perioda'))
    context.update(process_period_filter(request, periodb_str, 'periodb'))
    if context['perioda'] > context['periodb']:
        context['perioda'], context['periodb'] = \
            context['periodb'], context['perioda']
    periods = MonthPeriod.all_from(context['perioda'], context['periodb'])
    context.update({'selected_periods': periods})

    context.update({
        'section': section_id,
        'section_name': SECTIONS.get(section_id),
        'elements': section.build_context(periods=periods,
                                          entity=context['entity'])
    })

    return render(request,
                  kwargs.get('template_name',
                             'analysis_section{}.html'.format(section_id)),
                  context)


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
        _fields = ('username', 'first_name', 'last_name', 'email',)
        kwargs['initial'] = model_to_dict(instance.user, _fields) \
            if instance is not None else None
        super(PartnerForm, self).__init__(*args, **kwargs)

        pfields = copy.copy(self.fields)
        self.fields = fields_for_model(User, _fields)
        for k, v in pfields.items():
            self.fields.update({k: v})

        if instance:
            self.fields['username'].widget.attrs['readonly'] = True

    def clean_username(self):
        cu = self.cleaned_data.get('username')
        if self.instance:
            return cu
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
                    email=form.cleaned_data.get('email'))
                passwd = random_password(True)
                user.set_password(passwd)
                user.save()

                partner = Partner.objects.create(
                    user=user,
                    organization=form.cleaned_data.get('organization'),
                    can_upload=form.cleaned_data.get('can_upload'),
                    upload_location=form.cleaned_data.get('upload_location')
                    )

            messages.success(request,
                             _("New User account “{name}” created with "
                               "login `{username}` and password `{password}`")
                             .format(name=partner, username=partner.username,
                                     password=passwd))
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


@staff_member_required
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
                partner.user.save()

                partner.organization = form.cleaned_data.get('organization')
                partner.can_upload = form.cleaned_data.get('can_upload')
                partner.upload_location = \
                    form.cleaned_data.get('upload_location')
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


@staff_member_required
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
    return redirect('users')


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


def get_entity_detail(request, entity_uuid=None):
    entity = Entity.get_or_none(entity_uuid)

    if entity is None:
        data = None
    else:
        data = entity.to_dict()

    return JsonResponse(data, safe=False)


def get_entity_children(request, parent_uuid=None):
    """ generic view to build json results of entities children list """

    return HttpResponse(json.dumps(
        [Entity.get_or_none(e.uuid).to_dict()
         for e in Entity.get_or_none(parent_uuid).get_children()]),
        content_type='application/json')


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
