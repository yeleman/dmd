#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime
import calendar
from collections import OrderedDict

from django.db import models

logger = logging.getLogger(__name__)


class MonthPeriod(models.Model):

    class Meta:
        app_label = 'dmd'
        unique_together = [('year', 'month')]
        ordering = ['year', 'month']

    YEARS = OrderedDict([(str(year), str(year)) for year in range(2014, 2025)])
    MONTHS = OrderedDict([(str(month).zfill(2), str(month).zfill(2))
                          for month in range(1, 13)])

    year = models.CharField(max_length=4, choices=YEARS.items())
    month = models.CharField(max_length=2, choices=MONTHS.items())

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    def to_tuple(self):
        return (self.strid, self)

    @property
    def iyear(self):
        return int(self.year)

    @property
    def imonth(self):
        return int(self.month)

    @property
    def strid(self):
        return "{y}-{m}".format(y=self.year, m=self.month)

    @property
    def dhis_strid(self):
        return "{y}{m}".format(y=self.year, m=self.month)

    @property
    def name(self):
        return self.start_on.strftime("%B %Y").decode('utf-8')
        # return "{y}-{m}".format(y=self.year, m=self.month)

    @property
    def start_on(self):
        return datetime.datetime(self.iyear, self.imonth, 1)

    @property
    def end_on(self):
        nbd = calendar.monthrange(self.iyear, self.imonth)[1]
        return self.start_on + datetime.timedelta(days=nbd, seconds=86399)

    @classmethod
    def get_or_none(cls, period_str):
        # make sure we understand both regular and DHIS
        period_str = period_str.replace('-', '')
        year = period_str[:4]
        month = period_str[4:]
        try:
            return cls.objects.get(year=year, month=month)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_or_create(cls, year, month):
        y = str(year).zfill(2)
        m = str(month).zfill(2)
        if y not in cls.YEARS.values():
            raise ValueError("Out of bound year")
        if m not in cls.MONTHS.values():
            raise ValueError("Out of bound month")

        p, _ = cls.objects.get_or_create(year=y, month=m)
        return p

    @classmethod
    def find_create_from(cls, adate):
        return cls.get_or_create(year=adate.year, month=adate.month)

    @classmethod
    def current(cls):
        return cls.find_create_from(datetime.datetime.now())

    @classmethod
    def all_till_now(cls, descending=False):
        pfrom = MonthPeriod.objects.first()
        l = cls.all_from(pfrom, None)
        if descending:
            return reversed(l)
        return l

    @classmethod
    def all_from(cls, period_from, period_to=None):
        if period_to is None:
            period_to = cls.current()
        if period_from > period_to:
            raise ValueError("Period From is after Period To")
        period = period_from
        periods = []
        while period <= period_to:
            periods.append(period)
            try:
                period = period.following()
            except ValueError:
                break
        return periods

    def previous(self):
        if self.imonth == 1:
            nmonth = 12
            nyear = self.iyear - 1
        else:
            nmonth = self.imonth - 1
            nyear = self.year
        return self.get_or_create(nyear, nmonth)

    def following(self):
        if self.imonth == 12:
            nmonth = 1
            nyear = self.iyear + 1
        else:
            nmonth = self.imonth + 1
            nyear = self.year
        return self.get_or_create(nyear, nmonth)

    def __lt__(self, other):
        try:
            return self.end_on < other.start_on
        except:
            return NotImplemented

    def __le__(self, other):
        try:
            return self.end_on <= other.end_on
        except:
            return NotImplemented

    def __eq__(self, other):
        try:
            return self.strid == other.strid
        except:
            return NotImplemented

    def __ne__(self, other):
        try:
            return self.start_on != other.start_on \
                or self.end_on != other.end_on
        except:
            return NotImplemented

    def __gt__(self, other):
        try:
            return self.start_on > other.end_on
        except:
            return NotImplemented

    def __ge__(self, other):
        try:
            return self.start_on >= other.start_on
        except:
            return NotImplemented
