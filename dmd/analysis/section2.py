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
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.caching import get_cached_data

logger = logging.getLogger(__name__)
SECTION_ID = 2
SECTION_NAME = "Complétude"


@login_required
def view(request, entity_uuid=None, period_str=None, periodb_str=None,
         indicator_slug=None, **kwargs):
    context = {'page': 'analysis_section2'}

    # handling entity
    context.update(process_entity_filter(request, entity_uuid))

    # handling periods
    context.update(process_period_filter(request, period_str, 'period'))

    context.update({
        'section': SECTION_ID,
        'section_name': SECTION_NAME,
        'arrivals': OrderedDict(
            [(indicator, get_cached_data('section2-arrivals',
                                         entity=context['entity'],
                                         period=context['period'],
                                         indicator=indicator))
             for indicator in Indicator.objects.all()])
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
