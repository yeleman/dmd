#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.utils import timezone
from django.core.management.base import BaseCommand
from optparse import make_option

from dmd.models.Indicators import Indicator
from dmd.models.DataRecords import DataRecord
from dmd.utils import chdir_dmd

DEBUG = False
logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-d',
                    help='debug output by displaying creation records',
                    action='store_true',
                    default=False,
                    dest='debug'),
    )

    def handle(self, *args, **options):

        # make sure we're at project root
        chdir_dmd()

        logger.info("Auto-validation started...")

        DEBUG = options.get('debug', False)

        now = timezone.now()

        # loop on non-validated DataRecord
        records = DataRecord.objects \
            .filter(validation_status=DataRecord.NOT_VALIDATED,
                    indicator__origin=Indicator.MANUAL)

        logger.info("On {on}, there are {nb} non-validated DataRecords"
                    .format(on=now, nb=records.count()))

        for dr in records:

            # continue if validation delay is not over
            if not dr.validation_period_is_over():
                if DEBUG:
                    logger.debug("Not validating {dr} until {date}".format(
                        dr=dr,
                        date=dr.validation_deadline.strftime('%c')
                                                   .decode('utf-8')))
                continue

            # auto-validate
            dr.auto_validate(on=now)

            logger.debug("Auto-validated {}".format(dr))

        logger.info("done.")
