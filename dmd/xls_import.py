#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

import xlrd
from py3compat import text_type
from django.utils.translation import ugettext as _

from dmd.models import MonthPeriod, Entity, Indicator

logger = logging.getLogger(__name__)


class ExcelValueMissing(ValueError):
    pass


class ExcelValueError(ValueError):
    pass


class IncorrectExcelFile(ValueError):
    pass


def get_xls_sheet(filepath):
    try:
        return xlrd.open_workbook(filepath).sheet_by_name('indicateurs')
    except xlrd.XLRDError:
        raise IncorrectExcelFile(_("Not a proper XLS Template."))


def read_xls(filepath, meta_only=False):
    ws = get_xls_sheet(filepath)
    metadata = read_xls_metadata(filepath, ws)
    if meta_only:
        return metadata

    return read_xls_data(filepath, ws, metadata)


def read_xls_metadata(filepath, ws=None):

    if ws is None:
        ws = get_xls_sheet(filepath)

    cd = lambda row, column: text_type(ws.row_values(row)[column]).strip()

    # retrieve metadata
    meta = {
        'dps': cd(0, 3),  # D1
        'zs': cd(1, 3),  # D2
        'as': cd(2, 3),  # D3
        'year': cd(1, 5),  # F1
        'month': cd(0, 5),  # F2
    }

    # cleanup and presence check
    for field, value in meta.items():
        meta.update({field: value})
        if not value and not field == 'as':
            raise ExcelValueMissing(_("Field `{field}` is blank yet mandatory")
                                    .format(field))

    # retrieve period
    try:
        meta['year'] = int(float(meta['year']))
    except:
        raise ExcelValueError(_("Year value `{year}` is not valid")
                              .format(meta['year']))

    try:
        meta['month'] = int(meta['month'].split('-')[0].strip())
    except:
        raise ExcelValueError(_("Month value `{month}` is not valid")
                              .format(meta['month']))

    try:
        meta['period'] = MonthPeriod.get_or_create(meta['year'], meta['month'])
    except ValueError:
        raise ExcelValueError(_("Year/Month tuple `{year}-{month}` "
                                "is not valid")
                              .format(meta['year'], meta['month']))

    def find_location(meta):
        for field in ['dps', 'zs', 'as']:
            if not meta[field] or meta[field].lower() == "aucun":
                meta[field] = None

        if meta['dps'] is not None:
            meta['dps_entity'] = Entity.find_with_type(Entity.PROVINCE,
                                                       meta['dps'])
            if meta['dps_entity'] is None:
                raise ExcelValueError(_("Unable to match DPS `{dps}`")
                                      .format(meta['dps']))
        else:
            # no DPS, we're looking for RDC
            return Entity.objects.get(level=0)

        if meta['zs'] is not None:
            meta['zs_entity'] = Entity.find_with_type(Entity.ZONE, meta['zs'],
                                                      meta['dps_entity'])
            if meta['zs'] is None:
                raise ExcelValueError(_("Unable to match ZS `{zs}`")
                                      .format(meta['zs']))
        else:
            return meta['dps_entity']

        if meta['as'] is not None:
            meta['as_entity'], meta['as_candidates'] = \
                Entity.lookup_at(meta['zs_entity'], meta['as'])
        else:
            return meta['zs_entity']

        return meta['as_entity']

    meta['entity'] = find_location(meta)

    return meta


def read_xls_data(filepath, ws=None, meta=None):

    if ws is None:
        ws = get_xls_sheet(filepath)

    if meta is None:
        meta = read_xls_metadata(filepath, ws)

    cd = lambda row, column: ws.row_values(row)[column]

    # keep metadata
    data = {'meta': meta}

    for row in range(0, 100):

        # first col is Indicator.number
        try:
            number = cd(row, 0)
        except IndexError:
            continue

        # no-number means not a used line
        if not number:
            continue
        else:
            try:
                number = int(number)
            except:
                pass
            finally:
                number = text_type(number).zfill(2)

        num = cd(row, 4)
        denum = cd(row, 5)

        # skip if missing numerator or denominator
        if not num or not denum:
            continue

        indic = Indicator.get_by_number(number)
        # not an expected number
        if indic is None:
            continue

        try:
            num = float(num)
            denum = float(denum)
        except:
            raise ExcelValueError(_("Incorrect numerator or denominator value "
                                    "`{num} / {denom}` for: {indic}")
                                  .format(num, denum, indic.name))

        data.update({indic.slug: {'numerator': num, 'denominator': denum}})

    return data
