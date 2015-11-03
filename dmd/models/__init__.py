#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.db import models
from py3compat import text_type

from dmd.models.DataRecords import DataRecord
from dmd.models.Entities import Entity
from dmd.models.Indicators import Indicator
from dmd.models.Partners import Organization, Partner
from dmd.models.Periods import MonthPeriod

logger = logging.getLogger(__name__)


class Metadata(models.Model):

    class Meta:
        app_label = 'dmd'

    key = models.CharField(max_length=128, primary_key=True)
    value = models.CharField(max_length=512)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key

    @classmethod
    def get_or_none(cls, key):
        try:
            return cls.objects.get(key=key)
        except cls.DoesNotExist:
            return None

    @classmethod
    def nb_records(cls):
        try:
            return int(cls.objects.get(key='nb_records'))
        except cls.DoesNotExist:
            return None

    @classmethod
    def update(cls, key, value):
        qs = cls.objects.filter(key=key)
        if not qs.count():
            return cls.objects.create(key=key, value=text_type(value))
        else:
            inst = qs.get()
            inst.value = text_type(value)
            inst.save()
            return inst
