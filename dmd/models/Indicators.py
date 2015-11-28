#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from babel.numbers import format_decimal

from dmd.models.Entities import Entity
from dmd.models.Periods import MonthPeriod

logger = logging.getLogger(__name__)


class Indicator(models.Model):

    class Meta:
        app_label = 'dmd'
        ordering = ['number', 'name']

    PVC = 'pvc'
    CM = 'cm'
    BCC = 'bcc'
    SME = 'sme'
    HSS = 'hss'

    TECH_AREAS_1 = {
        PVC: _("Prevention Vector Control"),
        CM: _("Case Management"),
        BCC: _("Behavioral Chance Communication"),
        SME: _("Surveillance and M&E"),
        HSS: _("Health System Strengthening"),
    }

    ITN = 'itn/llin'
    PSM = 'psm'
    IPTP = 'iptp'
    IRS = 'irs'
    DIAGNOSIS = 'diagnosis'
    TREATMENT = 'treatment'
    CAPACITY_BUILDING = 'capacity_building'
    COMM_CASE_MGMT = 'community_case_management'
    KNOWLEDGE = 'knowledge'
    SUPERVISION = 'supervision'
    ENVIRONMENT = 'enable_environment'

    TECH_AREAS_2 = {
        ITN: _("ITN/LLIN"),
        PSM: _("PSM"),
        IPTP: _("IPTp"),
        IRS: _("IRS"),
        DIAGNOSIS: _("Diagnosis"),
        TREATMENT: _("Treatment"),
        CAPACITY_BUILDING: _("Capacity building"),
        COMM_CASE_MGMT: _("Community Case Management"),
        KNOWLEDGE: _("Knowledge"),
        SUPERVISION: _("Supervision"),
        ENVIRONMENT: _("Enable environment"),
    }

    EFFECT = 'effect'
    PROCESS = 'process'

    CATEGORIES = {
        EFFECT: _("Effect"),
        PROCESS: _("Process")
    }

    NUMBER = 'number'
    PERCENTAGE = 'percentage'
    PER_THOUSAND = 'per_thousand'
    PER_TEN_THOUSAND = 'per_ten_thousand'
    PER_HUNDRED_THOUSAND = 'per_hundred_thousand'
    PROPORTION = 'proportion'

    TYPES = {
        NUMBER: _("Number"),
        PERCENTAGE: _("Percentage"),
        PROPORTION: _("Proportion"),
        PER_THOUSAND: _("Per 1,000"),
        PER_TEN_THOUSAND: _("Per 10,000"),
        PER_HUNDRED_THOUSAND: _("Per 100,000"),
    }

    TYPES_COEFFICIENT = {
        NUMBER: 1,
        PERCENTAGE: 100,
        PER_THOUSAND: 1000,
        PER_TEN_THOUSAND: 10000,
        PER_HUNDRED_THOUSAND: 100000,
    }

    INTEGER_FORMAT = "#,##0;-#"
    FLOAT_2DEC_FORMAT = "#,##0.##;-#"
    FLOAT_1DEC_FORMAT = "#,##0.#;-#"

    NUMBER_FORMATS = {
        INTEGER_FORMAT: _("Integer"),
        FLOAT_1DEC_FORMAT: _("Float, precision 1"),
        FLOAT_2DEC_FORMAT: _("Float, precision 2"),
    }

    RAW_FMT = '{value}'
    PERCENT_FMT = '{value}%'
    PROPORTION_FMT = '{numerator}/{denominator}'
    PER_THOUSAND_FMT = '{value}/1 000'
    PER_TEN_THOUSAND_FMT = '{value}/10 000'
    PER_HUNDRED_THOUSAND_FMT = '{value}/100 000'
    VALUE_FORMATS = {
        RAW_FMT: "x",
        PERCENT_FMT: "x%",
        PER_THOUSAND_FMT: "x/1000",
        PER_TEN_THOUSAND_FMT: "x/10 000",
        PER_HUNDRED_THOUSAND_FMT: "x/100 000",
        PROPORTION_FMT: "a/b",
    }

    MANUAL = 'manual'
    DHIS = 'dhis'
    ORIGINS = {
        MANUAL: _("Manual"),
        DHIS: _("DHIS"),
    }

    SURVEY = 'survey'
    ROUTINE = 'routine'

    COLLECTION_TYPES = {
        SURVEY: _("Survey"),
        ROUTINE: _("Routine"),
    }

    slug = models.SlugField(max_length=255, primary_key=True)
    origin = models.CharField(max_length=64, choices=ORIGINS.items())
    number = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=512)
    name_en = models.CharField(max_length=512, blank=True, null=True)

    dhis_indicator_id = models.CharField(max_length=64, null=True, blank=True)
    dhis_numerator_id = models.CharField(max_length=64, null=True, blank=True)
    dhis_numerator_formula = models.CharField(
        max_length=512, null=True, blank=True)
    dhis_denominator_id = models.CharField(max_length=64,
                                           null=True, blank=True)
    dhis_denominator_formula = models.CharField(
        max_length=512, null=True, blank=True)

    category = models.CharField(max_length=64, choices=CATEGORIES.items(),
                                null=True, blank=True)
    tech_area1 = models.CharField(max_length=64,
                                  choices=TECH_AREAS_1.items(),
                                  null=True, blank=True)
    tech_area2 = models.CharField(max_length=64,
                                  choices=TECH_AREAS_2.items(),
                                  null=True, blank=True)
    itype = models.CharField(max_length=64, choices=TYPES.items())
    number_format = models.CharField(max_length=32,
                                     choices=NUMBER_FORMATS.items())
    value_format = models.CharField(max_length=64,
                                    choices=VALUE_FORMATS.items())
    organizations = models.ManyToManyField('Organization', blank=True,
                                           related_name='indicators')

    collection_type = models.CharField(max_length=64,
                                       choices=COLLECTION_TYPES.items())
    # mostly DPS for Survey, ZS for Routine
    collection_level = models.CharField(max_length=64,
                                        choices=Entity.TYPES.items())
    collection_period = models.PositiveIntegerField(
        help_text=_("In months"))

    # mostly PNLP, default 45d
    transmission_organizations = models.ManyToManyField(
        'Organization', blank=True, related_name='transmission_indicators')
    transmission_delay = models.PositiveIntegerField(
        blank=True, null=True, help_text=_("In days"))

    # mostly PNLP, default 10d
    validation_organizations = models.ManyToManyField(
        'Organization', blank=True, related_name='validation_indicators')
    validation_delay = models.PositiveIntegerField(
        blank=True, null=True, help_text=_("In days"))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __unicode__(self):
        return self.name

    @property
    def is_percent(self):
        return self.itype == self.PERCENTAGE

    @property
    def is_number(self):
        return self.itype == self.NUMBER

    @property
    def verbose_collection_type(self):
        return self.COLLECTION_TYPES.get(self.collection_type)

    @property
    def verbose_tech_area1(self):
        return self.TECH_AREAS_1.get(self.tech_area1)

    @property
    def verbose_tech_area2(self):
        return self.TECH_AREAS_2.get(self.tech_area2)

    @classmethod
    def get_all_dhis(cls):
        return cls.objects.filter(origin=cls.DHIS) \
            .exclude(dhis_denominator_id__isnull=True)

    @classmethod
    def get_all_manual(cls):
        return cls.objects.filter(origin=cls.MANUAL)

    @classmethod
    def get_all_surveys(cls):
        return cls.objects.filter(collection_type=cls.SURVEY)

    @classmethod
    def get_all_routine(cls, with_dhis=True):
        qs = cls.objects.filter(collection_type=cls.ROUTINE)
        if with_dhis:
            return qs
        return qs.filter(dhis_denominator_id__isnull=True)

    @classmethod
    def get_or_none(cls, slug):
        try:
            return cls.objects.get(slug=slug)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_by_id(cls, dhis_id):
        try:
            return cls.objects.get(origin=cls.DHIS, dhis_id=dhis_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_by_number(cls, number):
        try:
            return cls.objects.get(number=str(number))
        except cls.DoesNotExist:
            return None

    def to_dict(self):
        return {
            'slug': self.slug,
            'origin': self.origin,
            'number': self.number,
            'name': self.name,
        }

    def transmission_deadline(self, period):
        if self.transmission_delay:
            return period.end_on + datetime.timedelta(
                days=self.transmission_delay)
        elif self.collection_period:
            nb_weeks = self.collection_period * 4
            return period.end_on + datetime.timedelta(
                weeks=nb_weeks)
        return None

    def can_submit_on(self, on, period):
        if on < period.end_on:
            return False
        deadline = self.transmission_deadline(period)
        if deadline:
            return on < deadline
        return True

    def validation_deadline(self, period, created_on):
        if self.validation_delay:
            return created_on + datetime.timedelta(
                days=self.validation_delay)
        elif self.collection_period:
            nb_weeks = self.collection_period * 4
            return period.end_on + datetime.timedelta(
                weeks=nb_weeks)
        return None

    def format_number(self, value):
        if value is None:
            return None
        return format_decimal(value, format=self.number_format)

    def compute_value(self, numerator, denominator):
        if self.itype == self.PROPORTION:
            return numerator / denominator
        else:
            coef = self.TYPES_COEFFICIENT.get(self.itype)
            if coef is None:
                print(self.itype)
            try:
                return (numerator * coef) / denominator
            except ZeroDivisionError:
                raise

    def format_value(self, value, numerator, denominator):
        if value is None:
            return "n/a"
        fval = self.format_number(
            self.compute_value(numerator, denominator))
        numerator = self.format_number(numerator)
        denominator = self.format_number(denominator)
        return self.value_format.format(value=fval,
                                        numerator=numerator,
                                        denominator=denominator)

    def data_for(self, entity, year, month=None):
        qs = self.data_records.filter(entity=entity)
        if month is not None:
            period = MonthPeriod.get_or_create(year, month)
            dr = qs.get(period=period)
            return dr.to_dict()
        else:
            # calculate yearly aggregate
            periods = MonthPeriod.all_from(
                MonthPeriod.get_or_create(year, 1),
                MonthPeriod.get_or_create(year, 12))
            drs = qs.filter(period__in=periods)
            num_sum = sum([dr.numerator for dr in drs])
            denom_sum = sum([dr.denominator for dr in drs])
            try:
                value = self.compute_value(num_sum, denom_sum)
            except ZeroDivisionError:
                value = None
            return {
                # meta-data
                'kind': 'year-aggregate',
                'indicator': self,
                'period': None,
                'has_data': qs.count() > 0,
                'year': year,
                'periods': periods,
                'entity': entity,

                'numerator': num_sum,
                'denominator': denom_sum,
                'formatted_numerator': self.format_number(num_sum),
                'formatted_denominator': self.format_number(denom_sum),
                'value': value,
                'formatted': self.format_number(value),
                'human': self.format_value(value=value,
                                           numerator=num_sum,
                                           denominator=denom_sum)
            }
