#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from dmd.models.Periods import MonthPeriod
from dmd.models.DataRecords import DataRecord

logger = logging.getLogger(__name__)


def expected_entities_for(indicator, entity):
    # digital index of the level
    collection_level = entity.TYPES.keys().index(indicator.collection_level)
    # same level means source level
    if collection_level == entity.level:
        return [entity]
    # none expected at this level
    if collection_level < entity.level:
        return []

    return entity.get_descendants_of(indicator.collection_level)


def nb_expected_records_for(indicator, entity):
    return len(expected_entities_for(indicator, entity))


def agg_arrival_for_period(indicator, entity, period):
    return agg_arrival_for(indicator, entity, period.year, period.month)


def agg_arrival_for(indicator, entity, year, month):
    if month is not None:
        periods = [MonthPeriod.get_or_create(year, month)]
    else:
        periods = MonthPeriod.all_from(MonthPeriod.get_or_create(year, 1),
                                       MonthPeriod.get_or_create(year, 12))

    expected_entities = expected_entities_for(indicator, entity)

    qs = DataRecord.objects.filter(indicator=indicator,
                                   period__in=periods) \
                           .filter(entity__in=expected_entities)

    nb_expected_reports = len(expected_entities)
    nb_arrived_reports = qs.count()
    nb_prompt_reports = qs.filter(arrival_status=DataRecord.ARRIVED_ON_TIME) \
                          .count()

    return {
        'nb_expected_reports': nb_expected_reports,
        'nb_arrived_reports': nb_arrived_reports,
        'nb_prompt_reports': nb_prompt_reports,
        'completness': nb_arrived_reports / nb_expected_reports,
        'promptness': nb_prompt_reports / nb_expected_reports
    }
