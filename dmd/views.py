#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import tempfile
import json
import os

from py3compat import text_type
from django.http import JsonResponse, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from dmd.models import Entity, DataRecord, Partner, MonthPeriod
from dmd.xls_import import (read_xls, ExcelValueMissing,
                            ExcelValueError, IncorrectExcelFile)

logger = logging.getLogger(__name__)

STEP2_KEY = 'needs_entity_step2'
XLS_DATA_KEY = 'xls_data'


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
    data_file = forms.FileField(label="Fichier du rapport")


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
                message += _("\n{nb_created} records were created.")
            if nb_updated:
                message += _("\n{nb_updated} records were updated.")
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
    entity = forms.ChoiceField(label="Aire de Santé", choices=[])

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


@login_required
def raw_data(request, entity_uuid=None, period_str=None, *args, **kwargs):
    context = {'page': 'raw_data'}

    # handling entity
    root = Entity.objects.get(level=0)
    entity = Entity.get_or_none(entity_uuid) if entity_uuid else root
    if entity is None:
        raise Http404(request,
                      _("Unable to match entity `{}`").format(entity_uuid))

    def lineage_data_for(entity):
        if entity is None:
            return []
        lad = entity.lineage_data
        return [lad.get(ts, "") if ts != entity.etype else entity.uuid
                for ts in Entity.lineage()]

    context.update({
        'blank_uuid': "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        'root': root,
        'entity': entity,
        'lineage_data': lineage_data_for(entity),
        'lineage': Entity.lineage,
        'children': root.get_children(),
    })

    # handling period
    if period_str:
        period = MonthPeriod.get_or_none(period_str)
        if period is None:
            raise Http404(request,
                          _("Unable to match period with `{}`")
                          .format(period_str))
    else:
        period = MonthPeriod.current().previous()
    context.update({
        'periods': sorted([p.to_tuple() for p in MonthPeriod.all_till_now()],
                          reverse=True),
        'period': period,
    })

    context.update({
        'records': DataRecord.objects
                             .filter(entity=entity, period=period)
                             .order_by('indicator__number')
    })

    return render(request,
                  kwargs.get('template_name', 'raw_data.html'),
                  context)


@login_required
def data_export(request, *args, **kwargs):
    context = {'page': 'export'}

    return render(request,
                  kwargs.get('template_name', 'export.html'),
                  context)


@login_required
def analysis(request, *args, **kwargs):
    context = {'page': 'analysis'}

    return render(request,
                  kwargs.get('template_name', 'analysis.html'),
                  context)


@login_required
def users_list(request, *args, **kwargs):
    context = {'page': 'users',
               'partners': Partner.objects.all()}

    return render(request,
                  kwargs.get('template_name', 'users.html'),
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
