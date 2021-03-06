#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import copy
from pprint import pprint as pp

from django.core.management.base import BaseCommand
from optparse import make_option

from dmd.dhis_tools import get_dhis
from dmd.models.Entities import Entity
from dmd.models.Periods import MonthPeriod
from dmd.models.Indicators import Indicator
from dmd.models.DataRecords import DataRecord
from dmd.models.Partners import Partner
from dmd.utils import data_ident_for, chdir_dmd

DEBUG = True
NB_PREVIOUS_PERIODS = 3
logger = logging.getLogger(__name__)
dhisbot = Partner.get_or_none('dhisbot')


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-p',
                    help="Period (month) to fetch data for",
                    action='store',
                    dest='period'),
        make_option('-u',
                    help="Update data even if it exists",
                    action='store_true',
                    default=False,
                    dest='update'),
        make_option('-i',
                    help="Include previous {} periods"
                    .format(NB_PREVIOUS_PERIODS),
                    action='store_true',
                    default=False,
                    dest='previous'),
        make_option('-d',
                    help="debug output by displaying creation records",
                    action='store_true',
                    default=False,
                    dest='debug'),
    )

    def handle_record(self, jsdata, entity, periods):

        logger.info(periods)

        missing = '0.0'
        data = {}

        # loop on rows
        indic_data = {(indic_id, pid): val
                      for indic_id, pid, val in jsdata['rows']}
        for period in periods:
            pid = period.dhis_strid

            for indicator in Indicator.get_all_dhis():

                numerator = indic_data.get((indicator.dhis_numerator_id, pid))
                denominator = indic_data.get(
                    (indicator.dhis_denominator_id, pid))

                if numerator is None or numerator == missing:
                    logger.error("Missing numerator `{}` for `{}`"
                                 .format(indicator.dhis_numerator_id,
                                         indicator))
                    continue

                if not indicator.is_number and (denominator is None
                                                or denominator == missing):
                    logger.error("Missing denominator `{}` for `{}`"
                                 .format(indicator.dhis_denominator_id,
                                         indicator))
                    continue

                logger.debug(data_ident_for(indicator, period, entity))
                data.update({data_ident_for(indicator, period, entity): {
                    'slug': indicator.slug,
                    'period': period,
                    'entity': entity,
                    'numerator': numerator,
                    'denominator': denominator}})

        d = DataRecord.batch_create(data, dhisbot,
                                    source=DataRecord.DHIS,
                                    arrival_status=DataRecord.ARRIVED,
                                    auto_validate=True)
        if self.debug:
            pp(d)
        return d

    def no_record_at(self, entity, period):
        return DataRecord.objects.filter(entity=entity,
                                         period=period).count() == 0

    def handle(self, *args, **options):

        # make sure we're at project root
        chdir_dmd()

        # options parsing
        self.debug = options.get('debug')
        update = options.get('update')
        period = MonthPeriod.get_or_none(options.get('period'))
        if period is None:
            logger.error("Unable to match an actual period from `{}`"
                         .format(period))

        if options.get('previous', False):
            periods = []
            p = period
            while p > MonthPeriod.objects.all().first():
                periods.append(p)
                if len(periods) >= NB_PREVIOUS_PERIODS:
                    break
                p = p.previous()
        else:
            periods = [period]

        upath = '/analytics.json'

        indicators = {i.slug: (i.dhis_numerator_id, i.dhis_denominator_id)
                      for i in Indicator.get_all_dhis()}
        dhis_ids = list(set([v[0] for v in indicators.values()] +
                            [v[1] for v in indicators.values()]))

        drc = Entity.get_root()
        params = {
            'dimension': ['dx:{}'.format(";".join(dhis_ids)),
                          'pe:{}'.format(
                          ";".join([pe.dhis_strid for pe in periods]))],
            'filter': 'ou:{}'.format(drc.dhis_id),
            'displayProperty': 'NAME',
            'outputIdScheme': 'ID',
            'skipRounding': True,
        }

        logger.info(drc)
        if update or self.no_record_at(entity=drc, period=period):
            self.handle_record(get_dhis(path=upath, params=params),
                               entity=drc, periods=periods)

        for dps in drc.get_children():
            logger.info(dps)

            if not update and not self.no_record_at(entity=dps, period=period):
                continue

            dparams = copy.copy(params)
            dparams.update({'filter': 'ou:{}'.format(dps.dhis_id)})
            self.handle_record(get_dhis(path=upath, params=dparams),
                               entity=dps, periods=periods)

            # don't look for ZS if no data at DPS
            if self.no_record_at(entity=dps, period=period):
                continue

            for zs in dps.get_children():
                logger.info(zs)

                if not update and not self.no_record_at(entity=zs,
                                                        period=period):
                    continue

                zparams = copy.copy(params)
                zparams.update({'filter': 'ou:{}'.format(zs.dhis_id)})
                self.handle_record(get_dhis(path=upath, params=zparams),
                                   entity=zs, periods=periods)

                # don't look for ZS if no data at DPS
                if self.no_record_at(entity=zs, period=period):
                    continue

                for aire in zs.get_children():
                    logger.info(aire)

                    if not update and not self.no_record_at(entity=aire,
                                                            period=period):
                        continue

                    aparams = copy.copy(params)
                    aparams.update({'filter': 'ou:{}'.format(aire.dhis_id)})
                    self.handle_record(get_dhis(path=upath, params=aparams),
                                       entity=aire, periods=periods)
