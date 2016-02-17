#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from py3compat import text_type

from dmd.views.common import process_period_filter, process_entity_filter
from dmd.models.Periods import MonthPeriod
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.caching import get_cached_data

logger = logging.getLogger(__name__)
SECTION_ID = 2
SECTION_NAME = "Complétude"


@login_required
def view(request, entity_uuid=None, perioda_str=None, periodb_str=None,
         indicator_slug=None, **kwargs):
    context = {'page': 'analysis_section2'}

    # handling entity
    context.update(process_entity_filter(request, entity_uuid))

    # handling periods
    # context.update(process_period_filter(request, period_str, 'period'))
    context.update(process_period_filter(request, perioda_str, 'perioda'))
    context.update(process_period_filter(request, periodb_str, 'periodb'))
    if context['perioda'] > context['periodb']:
        context['perioda'], context['periodb'] = \
            context['periodb'], context['perioda']
    periods = MonthPeriod.all_from(context['perioda'], context['periodb'])
    context.update({'selected_periods': periods})

    def cached_data_list(entity, periods, indicator):
        return [get_cached_data('section2-arrivals',
                                entity=entity,
                                period=period,
                                indicator=indicator)
                for period in periods]

    context.update({
        'section': text_type(SECTION_ID),
        'section_name': SECTION_NAME,
        'arrivals': OrderedDict(
            [(indicator, cached_data_list(context['entity'],
                                          periods, indicator))
             for indicator in Indicator.get_all_routine()])
    })

    # evolution graph
    cp = {
        'periods': [period.to_tuple() for period in periods],
        'points': [get_cached_data('section2-points',
                                   entity=context['entity'], period=period)
                   for period in periods]
    }
    perioda = periods[0]
    periodb = periods[-1]
    context.update({
        'cp_title': "Évolution de la complétude à {name} entre {pa} et {pb}"
                    .format(name=context['entity'].short_name,
                            pa=perioda.strid,
                            pb=periodb.strid),
        'cp_fname': "completeness-_{pa}_{pb}"
                    .format(pa=perioda.strid, pb=periodb.strid),
        'cp_categories': [p[1].name for p in cp['periods']],
        'cp_series': [{'name': "Complétude", 'data': cp['points']}]
    })

    # absolute URI for links
    context.update({
        'baseurl': request.build_absolute_uri(),
        'lineage': [Entity.PROVINCE]})

    return render(request,
                  kwargs.get('template_name',
                             'analysis_section2.html'),
                  context)


def build_context(periods, entity):
    return {}
