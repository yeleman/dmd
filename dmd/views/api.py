#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import json
import os

from django.http import JsonResponse, HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.conf import settings

from dmd.views.common import process_period_filter
from dmd.views.misc import serve_exported_files
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.models.DataRecords import DataRecord
from dmd.gis import fname_for, gen_map_for

logger = logging.getLogger(__name__)


def get_entity_detail(request, entity_uuid=None):
    entity = Entity.get_or_none(entity_uuid)

    if entity is None:
        data = None
    else:
        data = entity.to_dict()

    return JsonResponse(data, safe=False)


def get_entity_children(request, parent_uuid=None):
    """ generic view to build json results of entities children list """

    return HttpResponse(json.dumps(
        [Entity.get_or_none(e.uuid).to_dict()
         for e in Entity.get_or_none(parent_uuid).get_children()]),
        content_type='application/json')


def single_geojson(request, entity_uuid):
    entity = Entity.get_or_none(entity_uuid)

    if entity is None:
        data = None
    else:
        data = entity.geojson

    return JsonResponse(data, safe=False)


def children_geojson(request, parent_uuid):
    parent = Entity.get_or_none(parent_uuid)

    if parent is None:
        data = None
    else:
        data = parent.children_geojson

    return JsonResponse(data, safe=False)


def indicator_list(request, col_type):

    if col_type not in Indicator.COLLECTION_TYPES.keys():
        raise Http404(_("Unknown collection type `{ct}`").format(ct=col_type))

    data = [ind.to_dict()
            for ind in Indicator.objects.filter(collection_type=col_type)]

    return JsonResponse(data, safe=False)


def json_data_record_for(request, period_str, entity_uuid, indicator_slug):

    entity = Entity.get_or_none(entity_uuid)
    if entity is None:
        raise Http404(_("Unknown entity UUID `{u}`").format(u=entity_uuid))

    period = process_period_filter(request, period_str, 'period').get('period')
    if period is None:
        raise Http404(_("Unknown period `{p}`").format(p=period_str))

    indicator = Indicator.get_or_none(indicator_slug)
    if indicator is None:
        raise Http404(_("Unknown indicator `{s}`").format(s=indicator_slug))

    return JsonResponse(DataRecord.get_for(period, entity, indicator),
                        safe=False)


def png_map_for(request, period_str, entity_name, indicator_number,
                with_title=True, with_legend=True):

    entity = Entity.get_by_short_name(entity_name)
    if entity is None:
        raise Http404(_("Unknown entity with name `{u}`")
                      .format(u=entity_name))

    if period_str is None and indicator_number is None:
        period = None
        indicator = None
        with_title = False
        fname = "initial.png"
    else:
        with_title = True
        period = process_period_filter(
            request, period_str, 'period').get('period')
        if period is None:
            raise Http404(_("Unknown period `{p}`").format(p=period_str))

        indicator = Indicator.get_by_number(indicator_number)
        if indicator is None:
            raise Http404(_("Unknown indicator `{s}`")
                          .format(s=indicator_number))

        fname = fname_for(entity, period, indicator)

    fpath = os.path.join('png_map', fname)
    abspath = os.path.join(settings.EXPORT_REPOSITORY, fpath)

    logger.debug(abspath)

    if not os.path.exists(abspath):
        try:
            gen_map_for(entity, period, indicator,
                        save_as=abspath,
                        with_title=with_title,
                        with_index=with_title)
        except IOError:
            logger.error("Missing map png folder in exports.")
            raise

    # return redirect('export', fpath=fpath)
    return serve_exported_files(request, fpath=fpath)
