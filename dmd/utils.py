#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import re
import random

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

from dmd.emails import send_email

PASSWORD_LENGTH = 8
DUMB_PASSWORD_LENGTH = 4

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


def random_password(dumb=False):
    """ random password suitable for mobile typing """
    if not dumb:
        return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz1234567890')
                        for i in range(PASSWORD_LENGTH)])

    # dumb password
    num_chars = DUMB_PASSWORD_LENGTH
    letters = 'abcdefghijklmnopqrstuvwxyz'
    index = random.randint(0, len(letters) - 1)

    password = letters[index]
    num_chars -= 1
    while num_chars:
        num_chars -= 1
        index += 1
        try:
            password += letters[index]
        except IndexError:
            password += letters[index - len(letters)]
    postfix = random.randint(0, 9)
    password += str(postfix)
    return password


def import_path(name, failsafe=False):
    """ import a callable from full module.callable name """
    def _imp(name):
        modname, __, attr = name.rpartition('.')
        if not modname:
            # single module name
            return __import__(attr)
        m = __import__(modname, fromlist=[str(attr)])
        return getattr(m, attr)
    try:
        return _imp(name)
    except (ImportError, AttributeError) as exp:
        # logger.debug("Failed to import {}: {}".format(name, exp))
        if failsafe:
            return None
        raise exp


def data_ident_for(indicator, period, entity):
    return "{period}_{entity}_{slug}".format(period=period.strid,
                                             slug=indicator.slug,
                                             entity=entity.uuids)


def send_templated_email(tmpl, partner, password, creator=None):
    return send_email(
        recipients=partner.email,
        context={'partner': partner,
                 'creator': creator,
                 'password': password,
                 'url': get_full_url()},
        template='emails/{tmpl}.txt'.format(tmpl=tmpl),
        title_template='emails/title.{tmpl}.txt'.format(tmpl=tmpl))


def send_new_account_email(partner, password, creator=None):
    return send_templated_email('new_account', partner, password, creator)


def send_reset_password_email(partner, password, creator=None):
    return send_templated_email('reset_password', partner, password, creator)


def get_full_url(request=None, path=''):
    if path.startswith('/'):
        path = path[1:]
    return 'http{ssl}://{domain}/{path}'.format(
        domain=get_current_site(request).domain,
        path=path, ssl="s" if settings.DOMAIN_USES_HTTPS else '')
