#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.http import Http404
from django.utils.translation import ugettext as _
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings

from dmd.models import Metadata
from dmd.models.DataRecords import DataRecord

from dmd.views.common import process_period_filter, process_entity_filter

logger = logging.getLogger(__name__)


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
def raw_data_record(request, record_id, *args, **kwargs):
    context = {'page': 'raw_data'}

    dr = DataRecord.get_by_id(record_id)
    if dr is None:
        raise Http404(_("Unable to find DataRecord with ID `{id}`")
                      .format(id=record_id))

    context.update({'record': dr})

    return render(request,
                  kwargs.get('template_name', 'raw_data_record.html'),
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
            'export_xlsx_fname': settings.ALL_EXPORT_XLSX_FNAME,
        })

    return render(request,
                  kwargs.get('template_name', 'export.html'),
                  context)
