#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import json

from django.http import JsonResponse, HttpResponse

from dmd.models import Entity

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
