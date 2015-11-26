#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import StringIO
import sys

from django.core.management.base import BaseCommand
from django.conf import settings
import unicodecsv as csv

from dmd.models import DataRecord, Metadata

logger = logging.getLogger(__name__)


def get_records():
    return DataRecord.objects.valid().order_by(
        'period__year',
        'period__month',
        'entity__level',
        'entity__name',
        'indicator__number')


def get_csv_for(records_qs, save_to=None):
    headers = ["PERIOD", "INDIC-NUM", "LOCATION", "DPS", "ZS", "AS",
               "INDIC-SLUG", "NUMERATOR", "DENOMINATOR", "VALUE",
               "DISPLAY-VALUE", "INDIC-NAME"]
    empty = ""

    if save_to:
        stream = open(save_to, 'w')
    else:
        stream = StringIO.StringIO()
    csv_writer = csv.DictWriter(stream, fieldnames=headers)

    csv_writer.writeheader()

    for row, record in enumerate(records_qs):

        csv_writer.writerow({
            'PERIOD': record.period.strid,
            'INDIC-NUM': record.indicator.number,
            'LOCATION': record.entity.uuids,
            'DPS': getattr(record.entity.get_dps(), 'short_name', empty),
            'ZS': getattr(record.entity.get_zs(), 'short_name', empty),
            'INDIC-SLUG': record.indicator.slug,
            'NUMERATOR': record.numerator,
            'DENOMINATOR': record.denominator,
            'VALUE': record.value,
            'DISPLAY-VALUE': record.human(),
            'INDIC-NAME': record.indicator.name
        })
        sys.stdout.write("Exporting row #: {}   \r".format(row))
        sys.stdout.flush()

    stream.close()

    if save_to:
        return

    return stream


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        logger.info("Exporting all DataRecord to: {}"
                    .format(settings.ALL_EXPORT_PATH))
        qs = get_records()
        nb_records = qs.count()
        get_csv_for(qs, save_to=settings.ALL_EXPORT_PATH)

        Metadata.update('nb_records', nb_records)
