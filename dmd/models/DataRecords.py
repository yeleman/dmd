#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from dmd.models.Partners import Partner
from dmd.models.Indicators import Indicator

logger = logging.getLogger(__name__)


class DataRecord(models.Model):

    UPLOAD = 'upload'
    DHIS = 'dhis'
    AGGREGATION = 'aggregation'

    SOURCES = {
        UPLOAD: "Directe",
        DHIS: "DHIS",
        AGGREGATION: "Aggregation",
    }

    NOT_VALIDATED = 'not_validated'
    VALIDATED = 'validated'
    AUTO_VALIDATED = 'auto_validated'
    REJECTED = 'rejected'
    MODIFIED = 'modified'
    VALIDATION_STATUSES = {
        NOT_VALIDATED: _("Not Validated"),
        VALIDATED: ("Validated"),
        AUTO_VALIDATED: ("Auto Validated"),
        REJECTED: ("Rejected"),
        MODIFIED: ("Modified"),
    }

    VALIDATED_STATUSES = [VALIDATED, AUTO_VALIDATED, MODIFIED]

    class Meta:
        app_label = 'dmd'
        unique_together = (('indicator', 'period', 'entity'),)

    indicator = models.ForeignKey('Indicator', related_name='data_records')
    period = models.ForeignKey('MonthPeriod', related_name='data_records')
    entity = models.ForeignKey('Entity', related_name='data_records')

    numerator = models.FloatField()
    denominator = models.FloatField()

    source = models.CharField(max_length=128, choices=SOURCES.items())

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('Partner', related_name='records_created')

    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey('Partner', null=True, blank=True,
                                   related_name='records_updated')

    validation_status = models.CharField(
        max_length=128,
        choices=VALIDATION_STATUSES.items(),
        default=NOT_VALIDATED)
    validated_on = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey('Partner', null=True, blank=True,
                                     related_name='records_validated')

    sources = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        return "{i}@{p}".format(i=self.indicator, p=self.period)

    @property
    def source_verbose(self):
        return self.SOURCES.get(self.source)

    @property
    def validation_status_verbose(self):
        return self.VALIDATION_STATUSES.get(self.validation_status)

    @property
    def validated(self):
        return self.validation_status in self.VALIDATED_STATUSES

    @property
    def auto_validated(self):
        return self.validated_by == Partner.validation_bot()

    @property
    def aggregate(self):
        return self.source == self.AGGREGATION

    @property
    def value(self):
        return self.indicator.compute_value(self.numerator,
                                            self.denominator)

    @property
    def formatted(self):
        return self.indicator.format_number(self.value)

    @property
    def data_is_suspect(self):
        if self.denominator:
            return self.denominator < self.numerator
        return False

    @classmethod
    def get_or_none(cls, indicator, period, entity, only_validated=False):
        qs = cls.objects.filter(indicator=indicator,
                                period=period, entity=entity)
        if only_validated:
            qs = qs.filter(validation_status__in=cls.VALIDATED_STATUSES)
        try:
            return qs.get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_by_id(cls, drid):
        try:
            return cls.objects.get(id=drid)
        except cls.DoesNotExist:
            return None

    @classmethod
    def batch_create(cls, data, partner, auto_validate=False):

        # make sure we can rollback if something goes wrong
        with transaction.atomic():

            for ident, dp in data.items():

                # skip errors
                if ident == 'errors':
                    continue

                slug = dp['slug']
                period = dp['period']
                entity = dp['entity']

                indic = Indicator.get_or_none(slug)
                dr = cls.get_or_none(indicator=indic,
                                     period=period,
                                     entity=entity)

                num = dp['numerator']
                denum = dp['denominator']

                if dr and (dr.numerator != num or dr.denominator != denum):
                    old_values = {'numerator': dr.numerator,
                                  'denominator': dr.denominator}
                    action = 'updated'

                    dr.numerator = num
                    dr.denominator = denum
                    dr.record_update(partner)

                elif dr is None:
                    old_values = None
                    action = 'created'

                    dr = cls.objects.create(
                        indicator=indic,
                        period=period,
                        entity=entity,
                        numerator=num,
                        denominator=denum,
                        source=cls.UPLOAD,
                        created_by=partner)

                    if auto_validate:
                        dr.auto_validate(on=timezone.now())
                else:
                    # new data are identical to datarecord
                    continue

                data[ident].update({
                    'action': action,
                    'id': dr.id,
                    'previous': old_values})

        return data

    def record_validation(self, status, on, by):
        self.validation_status = status
        self.validated_on = on
        self.validated_by = by
        self.save()

    def validate(self, on, by):
        self.record_validation(status=self.VALIDATED, on=on, by=by)

    def reject(self, on, by):
        self.record_validation(status=self.REJECTED, on=on, by=by)

    def auto_validate(self, on):
        self.record_validation(status=self.AUTO_VALIDATED, on=on,
                               by=Partner.validation_bot())

    def record_update(self, partner):
        self.updated_on = timezone.now()
        self.updated_by = partner
        self.save()

    def edit(self, on, by, numerator, denominator):
        with transaction.atomic():
            self.numerator = numerator
            self.denominator = denominator
            self.record_update(by)
            self.record_validation(status=self.MODIFIED, on=on, by=by)

    def human(self):
        return self.indicator.format_value(value=self.value,
                                           numerator=self.numerator,
                                           denominator=self.denominator)

    def to_dict(self):
        return {
            'kind': 'data-record',
            'indicator': self.indicator,
            'period': self.period,
            'periods': None,
            'entity': self.entity,

            'numerator': self.numerator,
            'denominator': self.denominator,
            'value': self.value,
            'formatted': self.formatted,
            'human': self.human,
        }

    @property
    def validation_deadline(self):
        return self.indicator.validation_deadline(self.period, self.created_on)

    def validation_period_is_over(self, on=None):
        if on is None:
            on = timezone.now()
        val_dl = self.validation_deadline

        return on > val_dl if val_dl is not None else False
