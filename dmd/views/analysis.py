#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
from collections import OrderedDict

from django.http import Http404
from django.utils.translation import ugettext as _
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from dmd.models.Periods import MonthPeriod
from dmd.utils import import_path
from dmd.analysis import SECTIONS
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.views.common import process_period_filter, process_entity_filter
from dmd.analysis.section1 import get_timed_records
from dmd.caching import get_cached_data


logger = logging.getLogger(__name__)


@login_required
def analysis(request, section_id,
             entity_uuid=None, perioda_str=None, periodb_str=None,
             *args, **kwargs):
    ''' Generic view for simple sections using an entity and periods '''

    context = {'page': 'analysis_section{}'.format(section_id)}

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

    # absolute URI for links
    context.update({'baseurl': request.build_absolute_uri()})

    return render(request,
                  kwargs.get('template_name',
                             'analysis_section{}.html'.format(section_id)),
                  context)


@login_required
def map(request, *args, **kwargs):
    context = {'page': 'map'}
    drc = Entity.get_root()

    context.update({
        'root': drc,
        'periods': MonthPeriod.all_till_now(),
        'dps_list': drc.get_children()
    })

    return render(request, kwargs.get('template_name', 'map.html'), context)


@login_required
def dashboard(request, indicator_slug=None, period_str=None, *args, **kwargs):
    context = {'page': 'dashboard'}
    drc = Entity.get_root()

    context.update(process_period_filter(request, period_str, 'period'))
    if context['period'] is None:
        context['period'] = MonthPeriod.current().previous()

    all_indicators = Indicator.objects.all()
    indicator = Indicator.get_or_none(indicator_slug)

    context.update({
        'root': drc,
        'completeness': OrderedDict([
            (dps, get_cached_data('completeness',
                                  dps=dps, period=context['period'],
                                  indicator=indicator))
            for dps in drc.get_children()
        ]),
        'indicators': all_indicators,
        'indicator': indicator,
    })

    # evolution of pw_anc_receiving_sp3
    context.update({
        'pwsp3': get_timed_records(Indicator.get_by_number(59),
                                   drc, context['all_periods']),
        'perioda_str': context['all_periods'][0].strid,
        'periodb_str': context['all_periods'][-1].strid,
    })

    return render(request, kwargs.get('template_name', 'dashboard.html'),
                  context)
