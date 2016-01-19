#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.core.management.base import BaseCommand
from optparse import make_option

from dmd.models.Entities import Entity
from dmd.xlsx.xlexport import generate_dataentry_for
from dmd.utils import chdir_dmd


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-d',
                    help='DPS name to gen XLS for',
                    action='store',
                    default='BAS UELE',
                    dest='dps'),
    )

    def handle(self, *args, **options):

        # make sure we're at project root
        chdir_dmd()

        dps_name = options.get('dps')
        if not dps_name:
            logger.error("Unable to match DPS with name `{}`"
                         .format(dps_name))
            return 1

        rdc = Entity.get_root()
        dps = Entity.lookup_at(parent=rdc, name=dps_name)[0]
        if dps is None:
            logger.error("Unable to match DPS with name `{}`"
                         .format(dps_name))
            return 1

        logger.info("Generating XLS dataentry tool for `{}`"
                    .format(dps_name))

        generate_dataentry_for(dps, 'dataentry.xlsx')
