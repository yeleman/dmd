#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.http import Http404
from django.utils.translation import ugettext as _

from dmd.models.Entities import Entity
from dmd.models.Periods import MonthPeriod

logger = logging.getLogger(__name__)


def lineage_data_for(entity):
    if entity is None:
        return []
    lad = entity.lineage_data
    return [lad.get(ts, "") if ts != entity.etype else entity.uuid
            for ts in Entity.lineage()]


def process_period_filter(request, period_str=None, name='period'):
    if period_str:
        period = MonthPeriod.get_or_none(period_str)
        if period is None:
            raise Http404(request,
                          _("Unable to match period with `{period}`")
                          .format(period=period_str))
    else:
        period = MonthPeriod.current().previous()

    all_periods = MonthPeriod.all_till_now()
    return {
        'periods': sorted([p.to_tuple() for p in all_periods],
                          reverse=True),
        'all_periods': all_periods,
        name: period,
    }


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
