#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import json
import uuid
import re
from collections import OrderedDict

from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from py3compat import text_type

from dmd.utils import lookup_entity_at

logger = logging.getLogger(__name__)


class Entity(MPTTModel):

    class Meta:
        app_label = 'dmd'

    class MPTTMeta:
        order_insertion_by = ['name']

    PAYS = 'pays'
    PROVINCE = 'division_provinciale_sante'
    ZONE = 'zone_sante'
    AIRE = 'aire_sante'
    CENTRE = 'centre_sante'

    TYPES = OrderedDict([
        (PAYS, _("Country")),
        (PROVINCE, _("Division Provinciale de la Santé")),
        (ZONE, _("Zone de santé")),
        # (AIRE, _("Aire de Santé")),
        # (CENTRE, _("Centre de Santé")),
    ])

    uuid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4, editable=False)

    # DRC coding
    code = models.CharField(max_length=16, unique=True, null=True, blank=True)

    # labels
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=128)
    display_name = models.CharField(max_length=255)

    # DHIS-only fields
    dhis_level = models.PositiveIntegerField()
    dhis_id = models.CharField(max_length=64, unique=True)

    etype = models.CharField(max_length=64, choices=TYPES.items())
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children', db_index=True)

    # GIS
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    geometry = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        return self.name

    @property
    def uuids(self):
        return text_type(self.uuid)

    @property
    def std_name(self):
        cua = lambda value: re.sub(r'\s?Aire\s(de\s?)Sant[eé]', '',
                                   value, re.I)

        cuz = lambda value: re.sub(r'\s?Zone\s(de\s?)Sant[eé]', '',
                                   value, re.I)

        cud = lambda value: re.sub(r'\s?DPS', '',
                                   value, re.I)

        return cud(cuz(cua(self.name))).upper()

    @property
    def gps(self):
        return (self.latitude, self.longitude) \
            if self.latitude and self.longitude else None

    @property
    def geojson(self):
        return {
            "type": "Feature",
            "properties": self.to_dict(),
            "geometry": json.loads(self.geometry) if self.geometry else None
        }

    @property
    def children_geojson(self):
        return {
            "type": "FeatureCollection",
            "features": [child.geojson for child in self.get_children()]
        }

    @property
    def lineage_data(self):
        return {e.etype: e.uuid for e in self.get_ancestors()}

    @classmethod
    def get_root(cls):
        return cls.objects.get(level=0)

    @classmethod
    def get_by_id(cls, did):
        try:
            return cls.objects.get(dhis_id=did)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_none(cls, uuid):
        if not isinstance(uuid, basestring):
            uuid = str(uuid)
        try:
            return cls.objects.get(uuid=uuid)
        except (cls.DoesNotExist, ValueError):
            return None

    @classmethod
    def find_with_type(cls, etype, name, parent=None):
        qs = cls.objects.filter(etype=etype, name__iexact=name)
        if parent is not None:
            qs = qs.filter(parent=parent)
        try:
            return qs.get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def find_by_stdname(cls, std_name, parent):
        try:
            return {e.std_name: e for e in parent.get_children()}.get(std_name)
        except:
            return None

    @classmethod
    def lookup_at(cls, parent, name):
        return lookup_entity_at(parent, name)

    @classmethod
    def lineage(cls):
        return cls.TYPES.keys()[1:]

    @classmethod
    def clean_tree(cls, until):
        ''' ordered list of entity and children up to a type '''
        lineage = cls.TYPES.keys()
        break_on = lineage.index(until) + 1

        def loop_on(entity, break_on, descendants, level):
            if level == break_on:
                return

            for child in entity.get_children():
                if child.etype != lineage[level]:
                    continue
                descendants.append(child)
                loop_on(child, break_on, descendants, child.level + 1)

        descendants = []
        current = cls.get_root()
        descendants.append(current)
        loop_on(current, break_on, descendants, current.level + 1)

        return descendants

    @property
    def is_country(self):
        return self.etype == self.PAYS

    @property
    def is_dps(self):
        return self.etype == self.PROVINCE

    @property
    def is_zs(self):
        return self.etype == self.ZONE

    @property
    def is_as(self):
        return self.etype == self.AIRE

    def get_dps(self):
        return self.get_ancestor_of(self.PROVINCE)

    def get_zs(self):
        return self.get_ancestor_of(self.ZONE)

    def get_as(self):
        return self.get_ancestor_of(self.AIRE)

    def get_ancestor_of(self, etype):
        for ancestor in self.get_ancestors(include_self=True):
            if ancestor.etype == etype:
                return ancestor
        return None

    def fields(self):
        return ['uuid', 'code', 'name', 'short_name', 'display_name',
                'dhis_level', 'dhis_id', 'etype', 'parent']

    def to_dict(self):
        d = {field: unicode(getattr(self, field)) for field in self.fields()}
        d.update({'parent': str(self.parent.uuid) if self.parent else None})
        return d

    def to_tuple(self):
        return (self.uuid, self)

    def to_treed_tuple(self):
        if self.level > 0:
            prefix = ''.join(['-' for _ in range(self.level * 3)]) + ' '
        else:
            prefix = ''
        return self.uuid, "{prefix}{name}".format(prefix=prefix, name=self)
