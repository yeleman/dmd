#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import copy

from django.core.management.base import BaseCommand
from optparse import make_option

from dmd.dhis_tools import get_dhis
from dmd.models import Entity, MonthPeriod, Indicator, DataRecord, Partner

DEBUG = True
logger = logging.getLogger(__name__)
dhisbot = Partner.get_or_none('dhisbot')


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-p',
                    help='Period (month) to fetch data for',
                    action='store',
                    dest='period'),
        make_option('-u',
                    help='Update data even if it exists',
                    action='store_true',
                    default=False,
                    dest='update'),
        make_option('-d',
                    help='debug output by displaying creation records',
                    action='store_true',
                    default=False,
                    dest='debug'),
    )

    def handle_record(self, jsdata, entity, period):

        missing = '0.0'
        data = {
            'meta': {
                'period': period,
                'entity': entity,
            }
        }

        # loop on rows
        indic_data = {indic_id: val for indic_id, pid, val in jsdata['rows']}
        for indicator in Indicator.get_all_dhis():
            numerator = indic_data.get(indicator.dhis_numerator_id)
            denominator = indic_data.get(indicator.dhis_denominator_id)

            if numerator is None or numerator == missing:
                logger.error("Missing numerator `{}` for `{}`"
                             .format(indicator.dhis_numerator_id, indicator))
                continue

            if denominator is None or denominator == missing:
                logger.error("Missing denominator `{}` for `{}`"
                             .format(indicator.dhis_denominator_id, indicator))
                continue

            data.update({indicator.slug: {
                'numerator': numerator,
                'denominator': denominator}})

        d = DataRecord.batch_create(data, dhisbot)
        if self.debug:
            from pprint import pprint as pp ; pp(d)
        return d

    def no_record_at(self, entity, period):
        return DataRecord.objects.filter(entity=entity,
                                         period=period).count() == 0

    def handle(self, *args, **options):
        # options parsing
        self.debug = options.get('debug')
        update = options.get('update')
        period = MonthPeriod.get_or_none(options.get('period'))
        if period is None:
            logger.error("Unable to match an actual period from `{}`"
                         .format(period))

        upath = '/analytics.json'

        indicators = {i.slug: (i.dhis_numerator_id, i.dhis_denominator_id)
                      for i in Indicator.get_all_dhis()}
        dhis_ids = list(set([v[0] for v in indicators.values()] +
                            [v[1] for v in indicators.values()]))

        drc = Entity.get_root()
        params = {
            'dimension': ['dx:{}'.format(";".join(dhis_ids)),
                          'pe:{}'.format(period.dhis_strid)],
            'filter': 'ou:{}'.format(drc.dhis_id),
            'displayProperty': 'NAME',
            'outputIdScheme': 'ID',
            'skipRounding': True,
        }

        logger.info(drc)
        if update or self.no_record_at(entity=drc, period=period):
            self.handle_record(get_dhis(path=upath, params=params),
                               entity=drc, period=period)

        for dps in drc.get_children():
            logger.info(dps)

            if not update and not self.no_record_at(entity=dps, period=period):
                continue

            dparams = copy.copy(params)
            dparams.update({'filter': 'ou:{}'.format(dps.dhis_id)})
            self.handle_record(get_dhis(path=upath, params=dparams),
                               entity=dps, period=period)

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
                                   entity=zs, period=period)

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
                                       entity=aire, period=period)
