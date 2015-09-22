#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

AUTH = HTTPBasicAuth(settings.DHIS_USER, settings.DHIS_PASSWORD)
logger = logging.getLogger(__name__)
url_from_path = lambda path: "{}{}".format(settings.DHIS_BASE_URL, path)


def get_dhis(path, params={}, as_json=True):
    url = url_from_path(path)
    req = requests.get(url, auth=AUTH, params=params)

    try:
        req.raise_for_status()
    except Exception as e:
        try:
            jsd = req.json()
        except:
            jsd = None
        if jsd is not None and 'stats' in jsd.keys():
            logger.error("HTTP Error [h] in accessing {u}: {m}"
                         .format(h=req.status_code, u=url,
                                 m=jsd.get('message')))
        raise e
    if as_json:
        try:
            return req.json()
        except ValueError as e:
            logger.exception(e)
            logger.debug(req.text)
            raise
    else:
        return req.text
