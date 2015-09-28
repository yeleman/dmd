#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import StringIO
import sys

import xlwt
from django.core.management.base import BaseCommand
from django.conf import settings

from dmd.models import DataRecord, Metadata

logger = logging.getLogger(__name__)


def get_records():
    return DataRecord.objects.all().order_by(
        'period__year',
        'period__month',
        'entity__level',
        'entity__name',
        'indicator__number')


def get_xls_for(records_qs, save_to=None):
    wb = xlwt.Workbook()
    sheet = wb.add_sheet("data-records")

    headers = ["PERIOD", "INDIC-NUM", "LOCATION", "DPS", "ZS", "AS",
               "INDIC-SLUG", "NUMERATOR", "DENOMINATOR", "VALUE",
               "DISPLAY-VALUE", "INDIC-NAME"]
    empty = ""

    for col, item in enumerate(headers):
        sheet.write(0, col, item)

    for row, record in enumerate(records_qs):
        sys.stdout.write("Exporting row #: {}   \r".format(row))
        sys.stdout.flush()
        col = 0
        row += 1
        sheet.write(row, col, record.period.strid)
        col += 1
        sheet.write(row, col, record.indicator.number)
        col += 1
        sheet.write(row, col, record.entity.uuids)
        col += 1
        sheet.write(row, col, getattr(record.entity.get_dps(), 'name', empty))
        col += 1
        sheet.write(row, col, getattr(record.entity.get_zs(), 'name', empty))
        col += 1
        sheet.write(row, col, getattr(record.entity.get_as(), 'name', empty))
        col += 1
        sheet.write(row, col, record.indicator.slug)
        col += 1
        sheet.write(row, col, record.numerator)
        col += 1
        sheet.write(row, col, record.denominator)
        col += 1
        sheet.write(row, col, record.value)
        col += 1
        sheet.write(row, col, record.human())
        col += 1
        sheet.write(row, col, record.indicator.name)

    if save_to:
        wb.save(save_to)
        return

    stream = StringIO.StringIO()
    wb.save(stream)

    return stream


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        logger.info("Exporting all DataRecord to: {}"
                    .format(settings.ALL_EXPORT_PATH))
        qs = get_records()
        nb_records = qs.count()
        get_xls_for(qs, save_to=settings.ALL_EXPORT_PATH)

        Metadata.update('nb_records', nb_records)
