#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import re

logger = logging.getLogger(__name__)


def lookup_entity_at(parent, name):

    def cu(value):
        return re.sub(r'\s?Aire\s(de\s?)Sant[eé]', '', value, re.I).lower()

    children = parent.get_children()
    cname = cu(name)

    # look for exact matches after removing the clutter
    for child in children:
        if cu(child.name) == cname:
            return child, []

    # look for approximate matchs
    matchs = []
    for child in children:
        matchs.append((similarity_checker(cu(child.name), cname)[0], child))
    best = max(matchs, key=lambda x: x[0])

    if best[0] > 0.8:
        found = best[1]
    else:
        found = None

    return found, children


def similarity_checker(hay, needle):
    from difflib import SequenceMatcher as SM
    from nltk.util import ngrams

    needle_length = len(needle.split())
    max_sim_val = 0
    max_sim_string = ""

    for ngram in ngrams(hay.split(), needle_length + int(.2 * needle_length)):
        hay_ngram = " ".join(ngram)
        similarity = SM(None, hay_ngram, needle).ratio()
        if similarity > max_sim_val:
            max_sim_val = similarity
            max_sim_string = hay_ngram

    return max_sim_val, max_sim_string
