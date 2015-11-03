#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import json
import os

from django.core.management.base import BaseCommand
from optparse import make_option

from dmd.models import Entity

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-f',
                    help='GeoJSON file to import',
                    action='store',
                    dest='file'),
    )

    def handle(self, *args, **options):

        if not os.path.exists(options.get('file')):
            logger.error("GeoJSON file does not exit.")
            return False

        with open(options.get('file'), 'r') as f:
            gjson = json.load(f)

        rdc = Entity.get_root()

        for feature in gjson['features']:
            dps_name = feature['properties'].get('NOM_DPS')
            if dps_name:
                name = dps_name
                logger.debug(name)
                entity = Entity.objects.get(name=name)
            else:
                zs_name = feature['properties'].get('NAME')
                dps_name = feature['properties'].get('DPS')

                logger.debug("dps: {d} - zs: {z}"
                             .format(d=dps_name, z=zs_name))

                parent = Entity.find_by_stdname(parent=rdc, std_name=dps_name)
                logger.debug("\tparent: {p}".format(p=parent))
                assert parent is not None

                entity, children = Entity.lookup_at(parent=parent,
                                                    name=zs_name.upper())

            assert entity is not None
            logger.info(entity)

            entity.geometry = json.dumps(feature['geometry'])
            entity.save()

        logger.info("done.")
