#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import logging
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        # daily backups for last 7 days.
        # Monday backups for last 30 days.
        # first of each month

        today = datetime.datetime.today()
        aweek_ago = today - datetime.timedelta(days=7)
        amonth_ago = today - datetime.timedelta(days=30)

        for fname in os.listdir(settings.BACKUPS_REPOSITORY):
            if fname in ('.', '..', 'README'):
                continue

            if not fname.endswith('.7z'):
                continue

            fpath = os.path.join(settings.BACKUPS_REPOSITORY, fname)
            fdate = datetime.datetime(
                *[int(x)
                  for x in fname.rsplit('.7z', 1)[0]
                  .rsplit('_', 1)[1].split('-')])

            # keep all files less than a week old
            if fdate > aweek_ago:
                logger.info("Keeping {} - less than a week old".format(fname))
                continue

            # keep every mondays that are less than a month old
            if fdate.isoweekday() == 1 and fdate > amonth_ago:
                logger.info("Keeping {} - monday within a month".format(fname))
                continue

            # keep first of all month
            if fdate.day == 1:
                logger.info("Keeping {} - first of a month".format(fname))
                continue

            try:
                logger.info("Removing {}".format(fname))
                os.unlink(fpath)
            except OSError as exp:
                logger.error("Unable to delete {f}: {exp}"
                             .format(f=fpath, exp=exp))
