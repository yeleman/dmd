#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import os
import json

from django.core.management.base import BaseCommand
from optparse import make_option
from path import Path as p

from dmd.models.Entities import Entity


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('-p',
                    help='Path (folder) from which to import JSON files',
                    action='store',
                    default='./units',
                    dest='json_folder'),
    )

    def import_entity(self, eid, as_parent=False):
        logger.info("Importing #{}".format(eid))

        entity = Entity.get_by_id(eid)
        if entity:
            logger.debug("Already in DB.")
            return entity

        jsd = json.load(open(os.path.join(self.json_folder,
                                          "{}.json".format(eid))))

        if self.enforced_level is not None \
                and self.enforced_level < jsd.get('level'):
            logger.warning("Exiting. not at proper level")
            return

        all_groups = [oug['name']
                      for oug in jsd.get('organisationUnitGroups', [])]
        groups = [group
                  for group in all_groups
                  if group in Entity.TYPES.values()]
        if not groups:
            if 'DPS' in all_groups:
                groups.append("Division Provinciale de la Santé")
            else:
                logger.warning("Requested an unwanted entity (bad group)")
                return
        etype = [k for k, v in Entity.TYPES.items() if v == groups[0]][0]

        if etype is None:
            raise ValueError("Unable to guess type")

        if jsd.get('parent'):
            parent_id = jsd.get('parent').get('id')
            parent = Entity.get_by_id(parent_id)
            if parent is None:
                parent = self.import_entity(parent_id)
            if parent is None:
                raise ValueError("Unable to retrieve parent")
        else:
            parent = None

        entity = Entity.objects.create(
            uuid=jsd.get('uuid'),
            code=jsd.get('code'),

            name=jsd.get('name'),
            short_name=jsd.get('shortName'),
            display_name=jsd.get('displayName'),

            dhis_level=jsd.get('level'),
            dhis_id=jsd.get('id'),

            etype=etype,

            parent=parent)

        return entity

    def handle(self, *args, **options):
        self.json_folder = options.get('json_folder')

        logger.info("Importing Entities from JSON files from `{}`"
                    .format(self.json_folder))

        if not p(self.json_folder).isdir():
            logger.error("JSON folder `{}` is not a directory."
                         .format(self.json_folder))

        for level in range(5):
            self.enforced_level = level

            for fpath in os.listdir(self.json_folder):
                if not fpath.endswith('.json'):
                    continue

                # import entity
                eid = fpath[:-5]
                self.import_entity(eid)

        self.enforced_level = None
