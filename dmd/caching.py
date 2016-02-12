#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.core.cache import caches

from dmd.arrivals import (avg_arrival_for_period, agg_arrival_for_period,
                          agg_arrival_for_periods, completeness_point_for)

logger = logging.getLogger(__name__)
cache = caches['computations']


def compute_completeness_for(dps, period, indicator=None):
    if indicator:
        return agg_arrival_for_period(indicator, dps, period)
    else:
        return avg_arrival_for_period(dps, period)


def cache_exists_for(key, **kwargs):
    cache_key, _ = get_cache_details_for(key, **kwargs)
    return cache.get(cache_key, None) is not None


def get_cache_details_for(key, **kwargs):
    cache_key = None
    computer = lambda x: None

    if key == 'completeness':
        cache_key = 'json:completeness/{dps}/{period}/{indicator}'.format(
            dps=kwargs.get('dps').uuid,
            period=kwargs.get('period').strid,
            indicator=kwargs.get('indicator').slug
            if kwargs.get('indicator') else '-')
        computer = compute_completeness_for

    elif key == 'section2-arrivals':
        cache_key = 'json:section2-arrivals/{entity}/{perioda}_{periodb}' \
                    '/{indicator}' \
            .format(entity=kwargs.get('entity').uuid
                    if kwargs.get('entity') else '-',
                    perioda=kwargs.get('periods')[0].strid,
                    periodb=kwargs.get('periods')[-1].strid,
                    indicator=kwargs.get('indicator').slug)
        computer = agg_arrival_for_periods

    elif key == 'section2-points':
        cache_key = 'json:section2-points/{entity}/{period}' \
            .format(entity=kwargs.get('entity').uuid
                    if kwargs.get('entity') else '-',
                    period=kwargs.get('period').strid)
        computer = completeness_point_for

    return cache_key, computer


def get_cached_data(key, no_retry=False, **params):
    cache_key, computer = get_cache_details_for(key, **params)
    # cache.get_or_set(cache_key, computer(**params))  # dj1.9
    d = cache.get(cache_key, None)
    if d is None:
        update_cached_data(key, **params)
        if not no_retry:
            return get_cached_data(key, no_retry=True, **params)
    return d


def update_cached_data(key, **params):
    cache_key, computer = get_cache_details_for(key, **params)
    cache.set(cache_key, computer(**params), None)
