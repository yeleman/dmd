#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.contrib import admin
from django.contrib.sessions.models import Session

from dmd.models.Entities import Entity
from dmd.models.DataRecords import DataRecord
from dmd.models.Indicators import Indicator
from dmd.models.Periods import MonthPeriod
from dmd.models.Partners import Organization, Partner

admin.site.register(Entity)
admin.site.register(DataRecord)
admin.site.register(Indicator)
admin.site.register(MonthPeriod)
admin.site.register(Organization)
admin.site.register(Partner)

admin.site.register(Session)
