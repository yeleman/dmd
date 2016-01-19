#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from shapely.geometry import shape
from django.core.management.base import BaseCommand

from dmd.models.Entities import Entity
from dmd.utils import chdir_dmd

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        # make sure we're at project root
        chdir_dmd()

        logger.info("Creating latitude and longitude data for Entities")

        for entity in Entity.objects.all():
            if not entity.geometry:
                logger.debug("Skipping {}, no geometry.".format(entity))
                continue

            feature_geom = shape(entity.geojson['geometry'])
            feature_centroid = feature_geom.centroid
            entity.latitude = feature_centroid.x
            entity.longitude = feature_centroid.y
            entity.save()
            logger.info("{name}: {lat}, {lng}"
                        .format(name=entity.short_name,
                                lat=entity.latitude,
                                lng=entity.longitude))

        logger.info("done.")
