#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from dmd.views.common import process_period_filter, process_entity_filter
from dmd.models.Periods import MonthPeriod
from dmd.models.Indicators import Indicator
from dmd.models.DataRecords import DataRecord

logger = logging.getLogger(__name__)
SECTION_ID = 1
SECTION_NAME = "Évolution"


@login_required
def view(request, entity_uuid=None, perioda_str=None, periodb_str=None,
         indicator_slug=None, **kwargs):
    context = {'page': 'analysis_section1'}

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

    all_indicators = Indicator.objects.all()
    if indicator_slug:
        qs = all_indicators.filter(slug=indicator_slug)
        indicator = qs.get()
    else:
        qs = indicator = None

    context.update({
        'section': SECTION_ID,
        'section_name': SECTION_NAME,
        'elements': build_context(periods=periods,
                                  entity=context['entity'],
                                  qs=qs),
        'indicators': all_indicators,
        'indicator': indicator,
    })

    # absolute URI for links
    context.update({'baseurl': request.build_absolute_uri()})

    return render(request,
                  kwargs.get('template_name',
                             'analysis_section1.html'),
                  context)


def data_point_for(indicator, entity, period):
    dr = DataRecord.get_or_none(indicator=indicator,
                                period=period, entity=entity,
                                only_validated=True)

    return {
        'has_data': bool(getattr(dr, 'id', False)),
        'id': getattr(dr, 'id', None),
        'indicator': indicator,
        'entity': entity,
        'period': period,
        'numerator': getattr(dr, 'numerator', None),
        'denominator': getattr(dr, 'denominator', None),
        'value': getattr(dr, 'value', None),
        'formatted': getattr(dr, 'formatted', None),
        'formatted_numerator': getattr(dr, 'formatted_numerator', None),
        'formatted_denominator': getattr(dr, 'formatted_denominator', None),
        'human': getattr(dr, 'human', lambda: None)(),
    }


def get_timed_records(indicator, entity, periods):
    years = sorted(set([period.year for period in periods]))
    return {
        'indicator': indicator,
        'periods': [period.to_tuple for period in periods],
        'points': [data_point_for(indicator, entity, period)
                   for period in periods],
        'year_elements': [indicator.data_for(entity, year) for year in years],
    }


def build_context(entity, periods, qs=None, *args, **kwargs):
    qs = qs or Indicator.objects.all()
    return OrderedDict([(indicator.slug,
                         get_timed_records(indicator, entity, periods))
                        for indicator in qs])
