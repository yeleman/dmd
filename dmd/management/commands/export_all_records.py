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
from dmd.xlsx.xlexport import export_to_spreadsheet

logger = logging.getLogger(__name__)


def get_records():
    return DataRecord.objects.valid().order_by(
        'period__year',
        'period__month',
        'entity__level',
        'entity__name',
        'indicator__number')


def get_csv_for(records_qs, save_to=None):
    headers = ["PERIOD", "INDIC-NUM", "LOCATION", "DPS", "ZS",
               "INDIC-SLUG", "NUMERATOR", "DENOMINATOR", "VALUE",
               "DISPLAY-VALUE", "INDIC-NAME"]
    empty = ""

    if save_to:
        stream = open(save_to, 'w')
    else:
        stream = StringIO.StringIO()
    csv_writer = csv.DictWriter(stream, fieldnames=headers)

    csv_writer.writeheader()

    row = 0
    for record in records_qs.iterator():
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

        row += 1

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

        logger.info("Exporting all DataRecord (XLS 1sheet/indicator) to {}"
                    .format(settings.ALL_EXPORT_XLSX_PATH))

        export_to_spreadsheet(qs, save_to=settings.ALL_EXPORT_XLSX_PATH)

        Metadata.update('nb_records', nb_records)
