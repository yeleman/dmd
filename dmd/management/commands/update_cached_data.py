#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import sys

from django.core.management.base import BaseCommand

from dmd.models.Periods import MonthPeriod
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.caching import cache_exists_for, update_cached_data

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        logger.info("Updating cache for dashboard completeness...")

        periods = MonthPeriod.all_till_now()
        all_dps = Entity.get_root().get_children()
        indicators = Indicator.objects.all()
        all_indicators = list(indicators) + [None]
        nb_items = len(periods) * len(all_dps) * len(all_indicators)

        nb_ran = 0
        for period in periods:
            # logger.debug("{}".format(period))
            for dps in all_dps:
                # logger.debug("== {}".format(dps))
                for indicator in all_indicators:
                    nb_ran += 1
                    # logger.debug("==== {}".format(indicator))

                    params = {
                        'dps': dps,
                        'period': period,
                        'indicator': indicator
                    }

                    # existing cache 4months+ old are not regenerated
                    if period <= periods[-4]:
                        if cache_exists_for('completeness', **params):
                            # logger.info("***** Skipping existing.")
                            continue

                    update_cached_data('completeness', **params)

                    sys.stdout.write("{}/{} - {}%\r"
                                     .format(nb_ran, nb_items,
                                             int(nb_ran / nb_items * 100)))
                    sys.stdout.flush()

        logger.info("Updating cache for section2/arrivals...")

        nb_items = len(periods) * len(all_dps) * len(indicators)
        nb_ran = 0
        for period in periods:
            for dps in all_dps:
                for indicator in all_indicators:
                    if period <= periods[-4]:
                        if cache_exists_for('completeness', **params):
                            continue

                        update_cached_data('section2-arrivals',
                                           entity=dps,
                                           period=period,
                                           indicator=indicator)

                        sys.stdout.write("{}/{} - {}%\r"
                                         .format(nb_ran, nb_items,
                                                 int(nb_ran / nb_items * 100)))
                        sys.stdout.flush()

        logger.info("done.")
