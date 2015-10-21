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

from dmd.models import MonthPeriod
from dmd.utils import import_path
from dmd.analysis import SECTIONS
from dmd.views.common import process_period_filter, process_entity_filter

logger = logging.getLogger(__name__)


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
