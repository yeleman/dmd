#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import datetime

import numpy
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

    slug = models.SlugField(
        max_length=255, primary_key=True,
        verbose_name=_("Identifier"),
        help_text=_("Lowercase english summary without spaces"))
    origin = models.CharField(max_length=64, choices=ORIGINS.items(),
                              verbose_name=_("origin"),
                              help_text=_("Careful with DHIS indicators"))
    number = models.CharField(max_length=8, unique=True,
                              verbose_name=_("Indicator number"),
                              help_text=_("Respect convention"))
    name = models.CharField(max_length=512, verbose_name=_("French name"))
    name_en = models.CharField(max_length=512, blank=True, null=True,
                               verbose_name=_("English name"))

    dhis_indicator_id = models.CharField(max_length=64, null=True, blank=True,
                                         verbose_name=_("DHIS Indicator ID"),
                                         help_text=_("For reference only"))
    dhis_numerator_id = models.CharField(
        max_length=64, null=True, blank=True,
        verbose_name=_("DHIS Numerator ID"),
        help_text=_("Mandatory for DHIS Indicator"))
    dhis_numerator_formula = models.CharField(
        max_length=512, null=True, blank=True,
        verbose_name=_("DHIS Numerator Formula"),
        help_text=_("For reference only"))
    dhis_denominator_id = models.CharField(
        max_length=64, null=True, blank=True,
        verbose_name=_("DHIS Denominator ID"),
        help_text=_("Mandatory for DHIS Indicator"))
    dhis_denominator_formula = models.CharField(
        max_length=512, null=True, blank=True,
        verbose_name=_("DHIS Denominator Formula"),
        help_text=_("For reference only"))

    category = models.CharField(max_length=64, choices=CATEGORIES.items(),
                                null=True, blank=True,
                                verbose_name=_("Category"))
    tech_area1 = models.CharField(max_length=64,
                                  choices=TECH_AREAS_1.items(),
                                  null=True, blank=True,
                                  verbose_name=_("Tech Area 1"))
    tech_area2 = models.CharField(max_length=64,
                                  choices=TECH_AREAS_2.items(),
                                  null=True, blank=True,
                                  verbose_name=_("Tech Area 2"))
    itype = models.CharField(max_length=64, choices=TYPES.items(),
                             verbose_name=_("Indicator Type"))
    number_format = models.CharField(max_length=32,
                                     choices=NUMBER_FORMATS.items(),
                                     verbose_name=_("Number Format"))
    value_format = models.CharField(max_length=64,
                                    choices=VALUE_FORMATS.items(),
                                    verbose_name=_("Value Format"))
    organizations = models.ManyToManyField(
        'Organization', blank=True, related_name='indicators',
        verbose_name=_("Organizations"))

    collection_type = models.CharField(max_length=64,
                                       choices=COLLECTION_TYPES.items(),
                                       verbose_name=_("Collection Type"))
    # mostly DPS for Survey, ZS for Routine
    collection_level = models.CharField(max_length=64,
                                        choices=Entity.TYPES.items(),
                                        verbose_name=_("Collection Level"))
    collection_period = models.PositiveIntegerField(
        verbose_name=_("Collection Periodicity"),
        help_text=_("In months"))

    # mostly PNLP, default 90d
    transmission_organizations = models.ManyToManyField(
        'Organization', blank=True, related_name='transmission_indicators',
        verbose_name=_("Transmitting Organizations"))

    # mostly PNLP, default 45d
    prompt_transmission_delay = models.PositiveIntegerField(
        blank=True, null=True, help_text=_("In days"),
        verbose_name=_("Prompt Transmission Delay"))

    transmission_delay = models.PositiveIntegerField(
        blank=True, null=True, help_text=_("In days"),
        verbose_name=_("Transmission Delay"))

    # mostly PNLP, default 10d
    validation_organizations = models.ManyToManyField(
        'Organization', blank=True, related_name='validation_indicators',
        verbose_name=_("Validating Organizations"))
    validation_delay = models.PositiveIntegerField(
        blank=True, null=True, help_text=_("In days"),
        verbose_name=_("Validation Delay"))

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
    def verbose_origin(self):
        return self.ORIGINS.get(self.origin)

    @property
    def verbose_tech_area1(self):
        return self.TECH_AREAS_1.get(self.tech_area1)

    @property
    def verbose_tech_area2(self):
        return self.TECH_AREAS_2.get(self.tech_area2)

    @classmethod
    def get_all(cls):
        return cls.objects.all()

    @classmethod
    def get_all_dhis(cls):
        return cls.get_all().filter(origin=cls.DHIS) \
            .exclude(dhis_denominator_id__isnull=True)

    @classmethod
    def get_all_manual(cls):
        return cls.get_all().filter(origin=cls.MANUAL)

    @classmethod
    def get_all_surveys(cls):
        return cls.get_all().filter(collection_type=cls.SURVEY)

    @classmethod
    def get_all_routine(cls, with_dhis=True):
        qs = cls.get_all().filter(collection_type=cls.ROUTINE)
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
        # TODO: temporary bypass deadline check to catch up backlog
        return None
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

    def prompt_transmission_deadline(self, period):
        if self.prompt_transmission_delay:
            return period.end_on + datetime.timedelta(
                days=self.prompt_transmission_delay)
        return None

    def arrival_status_on(self, on, period):
        from dmd.models.DataRecords import DataRecord
        dl = self.prompt_transmission_deadline(period)

        if dl is None:
            return DataRecord.ARRIVED

        return DataRecord.ARRIVED_ON_TIME \
            if on < dl else DataRecord.ARRIVED_LATE

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
            try:
                return (numerator * coef) / denominator
            except ZeroDivisionError:
                # TODO: check what to do here
                return 0
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

    def year_data_for(self, entity, year, month=None):
        if month is not None:
            periods = [MonthPeriod.get_or_create(year, month)]
        else:
            periods = MonthPeriod.all_from(
                MonthPeriod.get_or_create(year, 1),
                MonthPeriod.get_or_create(year, 12))
        return self.data_for(entity, periods)

    def data_for(self, entity, periods):
        from dmd.models.DataRecords import DataRecord
        qs = self.data_records.filter(entity=entity) \
            .filter(validation_status__in=DataRecord.VALIDATED_STATUSES)
        if len(periods) == 1:
            dr = qs.get(period=periods[-1])
            return dr.to_dict()
        else:
            drs = qs.filter(period__in=periods)
            numerators = [dr.numerator for dr in drs]
            num_sum = sum(numerators)
            num_avg = numpy.mean(numerators) if numerators else 0
            denominators = [dr.denominator for dr in drs]
            denom_sum = sum(denominators)
            denom_avg = numpy.mean(denominators) if denominators else 0
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
                # 'year': year,
                'periods': periods,
                'entity': entity,

                'numerator_sum': num_sum,
                'denominator_sum': denom_sum,
                'numerator_avg': num_avg,
                'denominator_avg': denom_avg,

                'numerator_sum_fmt': self.format_number(num_sum),
                'denominator_sum_fmt': self.format_number(denom_sum),
                'numerator_avg_fmt': self.format_number(num_avg),
                'denominator_avg_fmt': self.format_number(denom_avg),

                'value': value,
                'formatted': self.format_number(value),
                'human': self.format_value(value=value,
                                           numerator=num_sum,
                                           denominator=denom_sum)
            }
