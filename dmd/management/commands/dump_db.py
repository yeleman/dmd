#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import os
import logging
import tempfile
import subprocess
import shutil

from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from optparse import make_option

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f',
                    help='GeoJSON file to import',
                    action='store',
                    dest='file'),
    )

    def handle(self, *args, **options):

        # django config of the DB
        dbconf = settings.DATABASES.get('default', {})

        if dbconf.get('ENGINE').endswith('mysql'):
            # dump the MySQL DB to a file
            dump_name = "{name}.sql".format(name=dbconf.get('NAME'))
            dump_path = os.path.join(settings.BACKUPS_REPOSITORY, dump_name)
            cmd = ['mysqldump',
                   '-h', dbconf.get('HOST'),
                   '-u', dbconf.get('USER'),
                   '-p', dbconf.get('PASSWORD'),
                   '-r', dump_path,
                   '-d', dbconf.get('NAME')]

            # dump database
            subprocess.call(cmd, shell=True)
        elif dbconf.get('ENGINE').endswith('sqlite3'):
            # copy sqlite DB to backup dir
            dump_name = os.path.basename(dbconf.get('NAME'))
            dump_path = os.path.join(settings.BACKUPS_REPOSITORY, dump_name)
            shutil.copy2(dbconf.get('NAME'), dump_path)
        else:
            logger.error("DB engine `{engine}` not supported"
                         .format(engine=dbconf.get('ENGINE')))

        # compression is done from backup dir
        curdir = os.getcwd()
        os.chdir(settings.BACKUPS_REPOSITORY)

        ark_name = "{orig}_{date}.7z".format(
            orig=os.path.basename(dump_path),
            date=timezone.now().strftime("%Y-%m-%d"))

        # compress the DB dump
        subprocess.call(['7z', 'a', ark_name, dump_name])

        # delete uncompressed file
        try:
            os.unlink(dump_path)
        except:
            pass

        # restore working dir
        os.chdir(curdir)
