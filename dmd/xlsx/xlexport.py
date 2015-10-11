#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import copy
import StringIO

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.dimensions import RowDimension, ColumnDimension
from openpyxl.styles import (PatternFill, Border, Side,
                             Alignment, Protection, Font)
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles.fills import FILL_SOLID

from dmd.xlsx import column_to_letter
from dmd.models import Entity, Indicator

logger = logging.getLogger(__name__)


def xl_col_width(cm):
    """ xlwt width for a given width in centimeters """
    return 4.725 * cm


def xl_set_col_width(sheet, column, cm):
    """ change column width """
    letter = column_to_letter(column)
    if column not in sheet.column_dimensions.keys():
        sheet.column_dimensions[letter] = \
            ColumnDimension(worksheet=sheet)
    sheet.column_dimensions[letter].width = xl_col_width(cm)


def xl_row_height(cm):
    """ xlwt height for a given height in centimeters """
    return 28.35 * cm


def xl_set_row_height(sheet, row, cm):
    """ change row height """
    if row not in sheet.row_dimensions.keys():
        sheet.row_dimensions[row] = RowDimension(worksheet=sheet)
    sheet.row_dimensions[row].height = xl_row_height(cm)


dataentry_fname_for = lambda dps: "saisie-PNLP-{}.xlsx".format(dps.std_name)


def generate_dataentry_for(dps, save_to=None):

    # colors
    black = 'FF000000'
    dark_gray = 'FFA6A6A6'
    light_gray = 'FFDEDEDE'
    yellow = 'F9FF00'

    # styles
    header_font = Font(
        name='Calibri',
        size=12,
        bold=True,
        italic=False,
        vertAlign=None,
        underline='none',
        strike=False,
        color=black)

    std_font = Font(
        name='Calibri',
        size=12,
        bold=False,
        italic=False,
        vertAlign=None,
        underline='none',
        strike=False,
        color=black)

    header_fill = PatternFill(fill_type=FILL_SOLID, start_color=dark_gray)
    yellow_fill = PatternFill(fill_type=FILL_SOLID, start_color=yellow)
    black_fill = PatternFill(fill_type=FILL_SOLID, start_color=black)
    odd_fill = PatternFill(fill_type=FILL_SOLID, start_color=light_gray)

    thin_black_side = Side(style='thin', color='FF000000')
    thick_black_side = Side(style='thick', color='FF000000')

    std_border = Border(
        left=thin_black_side,
        right=thin_black_side,
        top=thin_black_side,
        bottom=thin_black_side,
    )

    thick_left_border = Border(
        left=thick_black_side,
        right=thin_black_side,
        top=thin_black_side,
        bottom=thin_black_side,)
    thick_right_border = Border(
        right=thick_black_side,
        left=thin_black_side,
        top=thin_black_side,
        bottom=thin_black_side,)

    centered_alignment = Alignment(
        horizontal='center',
        vertical='center',
        text_rotation=0,
        wrap_text=False,
        shrink_to_fit=False,
        indent=0)

    left_alignment = Alignment(
        horizontal='left',
        vertical='center')

    vertical_alignment = Alignment(
        horizontal='left',
        vertical='bottom',
        text_rotation=90,
        wrap_text=True,
        shrink_to_fit=False,
        indent=0)

    number_format = '# ### ### ##0'

    protected = Protection(locked=True, hidden=False)
    unprotected = Protection(locked=False, hidden=False)

    header_style = {
        'font': header_font,
        'fill': header_fill,
        'border': std_border,
        'alignment': centered_alignment,
        'protection': protected
    }

    vheader_style = {
        'font': std_font,
        'alignment': vertical_alignment,
        'protection': protected
    }

    vheader_left_style = copy.copy(vheader_style)
    vheader_left_style.update({'border': thick_left_border})
    vheader_right_style = copy.copy(vheader_style)
    vheader_right_style.update({'border': thick_right_border})

    std_style = {
        'font': std_font,
        'border': std_border,
        'alignment': centered_alignment,
    }

    names_style = {
        'font': std_font,
        'border': std_border,
        'alignment': left_alignment,
    }

    def apply_style(target, style):
        for key, value in style.items():
            setattr(target, key, value)

    # data validations
    yv = DataValidation(type="list",
                        formula1='"{}"'.format(
                            ",".join([str(y) for y in range(2014, 2025)])),
                        allow_blank=True)
    mv = DataValidation(type="list",
                        formula1='"{}"'.format(
                            ",".join([str(y) for y in range(1, 13)])),
                        allow_blank=True)
    dv = DataValidation(type="whole", operator="greaterThanOrEqual",
                        formula1='0')

    wb = Workbook()
    ws = wb.active
    ws.title = "Données"

    ws.add_data_validation(yv)
    ws.add_data_validation(mv)
    ws.add_data_validation(dv)

    # resize row height for 0, 1
    xl_set_row_height(ws, 1, 2.2)
    xl_set_row_height(ws, 2, 2.2)

    # resize col A, B
    xl_set_col_width(ws, 1, 5.5)
    xl_set_col_width(ws, 2, 4.5)

    # write partial metadata headers
    ws.merge_cells("A3:A4")
    ws.cell("A3").value = "DPS"

    ws.merge_cells("B3:B4")
    ws.cell("B3").value = "ZS"

    ws.cell("C3").value = "ANNÉE"
    ws.cell("D3").value = "MOIS"

    indicator_column = 5
    dps_row = 5
    # zs_row = dps_row + 1

    # header style
    for sr in openpyxl.utils.cells_from_range("A3:D4"):
        for coord in sr:
            apply_style(ws.cell(coord), header_style)
    for coord in ["C4", "D4"]:
        ws.cell(coord).fill = yellow_fill
        ws.cell(coord).protection = unprotected

    # ZS of the selected DPS
    children = [child for child in dps.get_children()
                if child.etype == Entity.ZONE]

    def std_write(row, column, value, style=std_style):
        cell = ws.cell(row=row, column=column)
        cell.value = value
        apply_style(cell, style)

    # write indicator headers
    column = indicator_column
    for indicator in Indicator.get_all_manual():

        # write top header with indic name
        row = 1
        ws.merge_cells(start_row=row, end_row=row + 1,
                       start_column=column, end_column=column + 1)
        std_write(row, column, indicator.name, vheader_style)

        # write header with indic number
        row = 3
        num_str = "{n} - {t}".format(n=indicator.number,
                                     t=indicator.verbose_collection_type)
        ws.merge_cells(start_row=row, end_row=row,
                       start_column=column, end_column=column + 1)
        std_write(row, column, num_str, header_style)
        apply_style(ws.cell(row=row, column=column + 1), header_style)

        # write sub header with NUM/DENOM
        row = 4
        if indicator.itype == Indicator.NUMBER:
            ws.merge_cells(start_row=row, end_row=row,
                           start_column=column, end_column=column + 1)
            std_write(row, column, "NOMBRE", std_style)

            for r in range(row, row + len(children) + 2):  # DPS + children
                ws.merge_cells(start_row=r, end_row=r,
                               start_column=column, end_column=column + 1)
        else:
            std_write(row, column, "NUMERAT", std_style)
            std_write(row, column + 1, "DÉNOM", std_style)

        row = dps_row + len(children)

        # row-specific styles
        for r in range(1, row + 1):
            left = ws.cell(row=r, column=column)
            right = ws.cell(row=r, column=column + 1)

            # apply default style
            if r >= dps_row:
                apply_style(left, std_style)
                apply_style(right, std_style)
                left.number_format = number_format
                right.number_format = number_format

                # apply even/odd style
                if r % 2 == 0:
                    if column == indicator_column:
                        for c in range(1, indicator_column):
                            ws.cell(row=r, column=c).fill = odd_fill
                    ws.cell(row=r, column=column).fill = odd_fill
                    ws.cell(row=r, column=column + 1).fill = odd_fill

                # disable cell if data not expected at ZS
                if r > dps_row and indicator.collection_level != Entity.ZONE:
                    left.fill = black_fill
                    left.protection = protected
                    right.fill = black_fill
                    right.protection = protected
                else:
                    left.protection = unprotected
                    right.protection = unprotected

            # apply thick borders
            left.border = thick_left_border
            right.border = thick_right_border

        # iterate over indicator
        column += 2

    last_row = dps_row + len(children)

    # apply data validation for periods
    yv.ranges.append('C4:C{}'.format(last_row))
    mv.ranges.append('D4:D{}'.format(last_row))

    # apply positive integer validation to all cells
    last_column = indicator_column + len(Indicator.get_all_manual())
    last_letter = column_to_letter(last_column)
    dv.ranges.append('E4:{c}{r}'.format(c=last_letter, r=last_row))

    row = dps_row
    # write names & periods
    for zs in [None] + children:
        zs_name = zs.std_name if zs else "-"
        std_write(row, 1, dps.std_name, names_style)
        std_write(row, 2, zs_name, names_style)

        # set default value for period
        year = ws.cell(row=row, column=3)
        year.set_explicit_value(value="=$C$4",
                                data_type=year.TYPE_FORMULA)
        apply_style(year, std_style)
        year.protection = unprotected

        month = ws.cell(row=row, column=4)
        month.set_explicit_value(value="=$D$4",
                                 data_type=month.TYPE_FORMULA)
        apply_style(month, std_style)
        month.protection = unprotected

        row += 1

    ws.protection.set_password("PNLP")
    ws.protection.enable()

    if save_to:
        logger.info("saving to {}".format(save_to))
        wb.save(save_to)
        return

    stream = StringIO.StringIO()
    wb.save(stream)

    return stream
