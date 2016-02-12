#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
from collections import OrderedDict

import numpy
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
def dashboard(request, entity_uuid=None, indicator_slug=None,
              period_str=None, *args, **kwargs):
    context = {'page': 'dashboard'}

    # entity
    context.update(process_entity_filter(request, entity_uuid))
    root = context['entity'] if context['entity'] else Entity.get_root()

    context.update(process_period_filter(request, period_str, 'period'))
    if context['period'] is None:
        context['period'] = MonthPeriod.current().previous()

    all_indicators = Indicator.get_all_routine()
    indicator = Indicator.get_or_none(indicator_slug)

    context.update({
        'root': root,
        'completeness': OrderedDict([
            (child, get_cached_data('completeness',
                                    dps=child, period=context['period'],
                                    indicator=indicator))
            for child in root.get_children()
        ]),
        'indicators': all_indicators,
        'indicator': indicator,
        'lineage': [Entity.PROVINCE]
    })

    # totals
    context.update({
        'mean_completeness': numpy.mean(
            [e['completeness'] for e in context['completeness'].values()]),
        'mean_promptness': numpy.mean(
            [e['promptness'] for e in context['completeness'].values()]),
    })

    # evolution of pw_anc_receiving_sp3
    pwsp3 = get_timed_records(Indicator.get_by_number(59),
                              root, context['all_periods'])
    perioda = context['all_periods'][0]
    periodb = context['all_periods'][-1]

    context.update({
        'sp3_title': "{num} : {name} entre {pa} et {pb}"
                     .format(num=pwsp3['indicator'].number,
                             name=pwsp3['indicator'].name,
                             pa=perioda.strid,
                             pb=periodb.strid),
        'sp3_fname': "palu-evol-sp3-_{pa}_{pb}"
                     .format(pa=perioda.strid, pb=periodb.strid),
        'sp3_categories': [p[1].name for p in pwsp3['periods']],
        'sp3_series': [{'name': pwsp3['indicator'].name,
                        'data': pwsp3['points']}
                       ],
    })

    return render(request, kwargs.get('template_name', 'dashboard.html'),
                  context)
