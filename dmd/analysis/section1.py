#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
from collections import OrderedDict

from dmd.models.Indicators import Indicator
from dmd.models.DataRecords import DataRecord

logger = logging.getLogger(__name__)


def data_point_for(indicator, entity, period):
    dr = DataRecord.get_or_none(indicator=indicator,
                                period=period, entity=entity,
                                only_validated=True)
    # if dr is None:
    #     return None

    return {
        'id': getattr(dr, 'id', None),
        'indicator': indicator,
        'entity': entity,
        'period': period,
        'numerator': getattr(dr, 'numerator', None),
        'denominator': getattr(dr, 'denominator', None),
        'value': getattr(dr, 'value', None),
        'formatted': getattr(dr, 'formatted', None),
        'human': getattr(dr, 'human', lambda: None)()
    }


def get_timed_records(indicator, entity, periods):
    return {
        'indicator': indicator,
        'periods': [period.to_tuple for period in periods],
        'points': [data_point_for(indicator, entity, period)
                   for period in periods]
    }


def build_context(entity, periods, *args, **kwargs):
    return OrderedDict([(indicator.slug,
                         get_timed_records(indicator, entity, periods))
                        for indicator in Indicator.objects.all()])
