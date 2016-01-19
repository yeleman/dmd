#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime

from django.core.management.base import BaseCommand
from optparse import make_option
from py3compat import text_type

from dmd.models.DataRecords import DataRecord
from dmd.models.Partners import Partner
from dmd.utils import send_validation_feedback_email, chdir_dmd

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f',
                    help='GeoJSON file to import',
                    action='store',
                    dest='file'),
    )

    def handle(self, *args, **options):

        # make sure we're at project root
        chdir_dmd()

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        logger.info("Sending validation feedback for {}".format(yesterday))

        start = datetime.datetime(*yesterday.timetuple()[:6])
        end = datetime.datetime(*yesterday.timetuple()[:3],
                                hour=23, minute=59, second=59)

        dhis_bot = Partner.dhis_bot()

        records = DataRecord.objects \
            .exclude(created_by=dhis_bot) \
            .exclude(validated_by__isnull=True) \
            .filter(validated_on__gte=start,
                    validated_on__lte=end)

        def summary_for(partner):
            pqs = records.filter(created_by=partner)
            return {
                'partner': partner,
                'nb_validations': pqs.count(),
                'status': {
                    s['validation_status']: {
                        'name': text_type(DataRecord.VALIDATION_STATUSES.get(
                            s['validation_status'])),
                        'count': pqs.filter(
                            validation_status=s['validation_status']).count(),
                        'all': pqs.filter(
                            validation_status=s['validation_status'])
                    } for s in pqs.values('validation_status')
                }
            }

        feedbacks = [
            summary_for(Partner.objects.get(id=pid))
            for pid in set([r['created_by']
                            for r in records.values('created_by')])
            if pid
        ]

        for ptnf in feedbacks:
            partner = ptnf['partner']

            if not partner.email:
                continue

            ptnf.update({'yesterday': yesterday})
            email_sent, x = send_validation_feedback_email(
                partner=partner, summary=ptnf)
            if email_sent:
                logger.info("Sent feedback to {}".format(partner))
            else:
                logger.error("Unable to send feedback to {}".format(partner))

        logger.info("done.")
