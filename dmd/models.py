#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import uuid
import datetime
import calendar
from collections import OrderedDict

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey
from py3compat import text_type

from dmd.utils import lookup_entity_at

logger = logging.getLogger(__name__)


class Entity(MPTTModel):

    PAYS = 'pays'
    PROVINCE = 'division_provinciale_sante'
    ZONE = 'zone_sante'
    AIRE = 'aire_sante'
    CENTRE = 'centre_sante'

    TYPES = OrderedDict([
        (PAYS, "Pays"),
        (PROVINCE, "Division Provinciale de la Santé"),
        (ZONE, "Zone de santé"),
        (AIRE, "Aire de Santé"),
        # (CENTRE, "Centre de Santé"),
    ])

    class MPTTMeta:
        order_insertion_by = ['name']

    uuid = models.UUIDField(primary_key=True,
                            default=uuid.uuid4, editable=False)

    # DRC coding
    code = models.CharField(max_length=16, unique=True, null=True, blank=True)

    # labels
    name = models.CharField(max_length=256)
    short_name = models.CharField(max_length=128)
    display_name = models.CharField(max_length=256)

    # DHIS-only fields
    dhis_level = models.PositiveIntegerField()
    dhis_id = models.CharField(max_length=64, unique=True)

    etype = models.CharField(max_length=64, choices=TYPES.items())
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children', db_index=True)

    @property
    def uuids(self):
        return text_type(self.uuid)

    @classmethod
    def get_root(cls):
        return cls.objects.get(level=0)

    @classmethod
    def get_by_id(cls, did):
        try:
            return cls.objects.get(dhis_id=did)
        except cls.DoesNotExist:
            return None

    @classmethod
    def find_with_type(cls, etype, name, parent=None):
        qs = cls.objects.filter(etype=etype, name__iexact=name)
        if parent is not None:
            qs = qs.filter(parent=parent)
        try:
            return qs.get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def lookup_at(cls, parent, name):
        return lookup_entity_at(parent, name)

    @classmethod
    def get_or_none(cls, uuid):
        if not isinstance(uuid, basestring):
            uuid = str(uuid)
        try:
            return cls.objects.get(uuid=uuid)
        except (cls.DoesNotExist, ValueError):
            return None

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    def fields(self):
        return ['uuid', 'code', 'name', 'short_name', 'display_name',
                'dhis_level', 'dhis_id', 'etype', 'parent']

    def to_dict(self):
        d = {field: unicode(getattr(self, field)) for field in self.fields()}
        d.update({'parent': str(self.parent.uuid) if self.parent else None})
        return d

    def to_tuple(self):
        return (self.uuid, self)

    @classmethod
    def lineage(cls):
        return cls.TYPES.keys()[1:]

    @property
    def lineage_data(self):
        return {e.etype: e.uuid for e in self.get_ancestors()}

    def get_ancestor_of(self, etype):
        for ancestor in self.get_ancestors(include_self=True):
            if ancestor.etype == etype:
                return ancestor
        return None

    def get_dps(self):
        return self.get_ancestor_of(self.PROVINCE)

    def get_zs(self):
        return self.get_ancestor_of(self.ZONE)

    def get_as(self):
        return self.get_ancestor_of(self.AIRE)


class Organization(models.Model):
    slug = models.SlugField(max_length=96, primary_key=True)
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()


class Partner(models.Model):

    class Meta:
        ordering = ['user__last_name', 'user__first_name']

    user = models.OneToOneField(User)
    organization = models.ForeignKey(Organization)

    can_upload = models.BooleanField(default=False)
    upload_location = models.ForeignKey(Entity, null=True, blank=True)

    def with_org(self):
        if not self.organization:
            return str(self.user)
        return "{user}/{org}".format(user=str(self.user),
                                     org=str(self.organization))

    def __str__(self):
        username = self.username
        first_name = self.user.first_name.capitalize()
        last_name = self.user.last_name.upper()
        if first_name and last_name:
            return "{f} {l}".format(f=first_name, l=last_name)
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return username

    def __unicode__(self):
        return self.__str__()

    @property
    def username(self):
        return self.user.username

    @classmethod
    def get_or_none(cls, username):
        try:
            return cls.objects.get(user__username=username)
        except cls.DoesNotExist:
            return None


class MonthPeriod(models.Model):

    YEARS = OrderedDict([(str(year), str(year)) for year in range(2014, 2025)])
    MONTHS = OrderedDict([(str(month).zfill(2), str(month).zfill(2))
                          for month in range(1, 13)])

    class Meta:
        unique_together = [('year', 'month')]
        ordering = ['year', 'month']

    year = models.CharField(max_length=4, choices=YEARS.items())
    month = models.CharField(max_length=2, choices=MONTHS.items())

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

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

    def to_tuple(self):
        return (self.strid, self)

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


class Indicator(models.Model):

    PVC = 'pvc'
    CM = 'cm'
    BCC = 'bcc'
    SME = 'sme'
    HSS = 'hss'

    TECH_AREAS_1 = {
        PVC: "Prevention Vector Control",
        CM: "Case Management",
        BCC: "Behavioral Chance Communication",
        SME: "Surveillance and M&E",
        HSS: "Health System Strengthening",
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
        ITN: "ITN/LLIN",
        PSM: "PSM",
        IPTP: "IPTp",
        IRS: "IRS",
        DIAGNOSIS: "Diagnosis",
        TREATMENT: "Treatment",
        CAPACITY_BUILDING: "Capacity building",
        COMM_CASE_MGMT: "Community Case Management",
        KNOWLEDGE: "Knowledge",
        SUPERVISION: "Supervision",
        ENVIRONMENT: "Enable environment",
    }

    EFFECT = 'effect'
    PROCESS = 'process'

    CATEGORIES = {
        EFFECT: "Effet",
        PROCESS: "Processus"
    }

    NUMBER = 'number'
    PERCENTAGE = 'percentage'
    PER_THOUSAND = 'per_thousand'
    PER_TEN_THOUSAND = 'per_ten_thousand'
    PER_HUNDRED_THOUSAND = 'per_hundred_thousand'
    PROPORTION = 'proportion'

    TYPES = {
        NUMBER: "Nombre",
        PERCENTAGE: "Pourcentage",
        PROPORTION: "Proportion",
        PER_THOUSAND: "Pour 1000",
        PER_TEN_THOUSAND: "Pour 10 000",
        PER_HUNDRED_THOUSAND: "Pour 100 000",
    }

    TYPES_COEFFICIENT = {
        NUMBER: 1,
        PERCENTAGE: 100,
        PER_THOUSAND: 1000,
        PER_TEN_THOUSAND: 10000,
        PER_HUNDRED_THOUSAND: 100000,
    }

    INTEGER_FORMAT = "{:.0f}"
    FLOAT_2DEC_FORMAT = "{:.2f}"
    FLOAT_1DEC_FORMAT = "{:.1f}"

    NUMBER_FORMATS = {
        INTEGER_FORMAT: "Entier",
        FLOAT_1DEC_FORMAT: "Réel une décimale",
        FLOAT_2DEC_FORMAT: "Réel deux décimales",
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
        MANUAL: "Manuelle",
        DHIS: "DHIS",
    }

    class Meta:
        ordering = ['number', 'name']

    slug = models.SlugField(max_length=256, primary_key=True)
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
    organizations = models.ManyToManyField('Organization', blank=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

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

    def format_number(self, value):
        return self.number_format.format(value)

    def compute_value(self, numerator, denominator):
        if self.itype == self.PROPORTION:
            return numerator / denominator
        else:
            coef = self.TYPES_COEFFICIENT.get(self.itype)
            if coef is None:
                print(self.itype)
            return (numerator * coef) / denominator

    def format_value(self, value, numerator, denominator):
        fval = self.format_number(
            self.compute_value(numerator, denominator))
        numerator = self.format_number(numerator)
        denominator = self.format_number(denominator)
        return self.value_format.format(value=fval,
                                        numerator=numerator,
                                        denominator=denominator)

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

    @property
    def is_percent(self):
        return self.itype == self.PERCENTAGE


class DataRecord(models.Model):

    UPLOAD = 'upload'
    DHIS = 'dhis'
    AGGREGATION = 'aggregation'

    SOURCES = {
        UPLOAD: "Directe",
        DHIS: "DHIS",
        AGGREGATION: "Aggregation",
    }

    class Meta:
        unique_together = (('indicator', 'period', 'entity'),)

    indicator = models.ForeignKey(Indicator, related_name='data_records')
    period = models.ForeignKey(MonthPeriod, related_name='data_records')
    entity = models.ForeignKey(Entity, related_name='data_records')

    numerator = models.FloatField()
    denominator = models.FloatField()

    source = models.CharField(max_length=128, choices=SOURCES.items())

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Partner, related_name='records_created')

    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.ForeignKey(Partner, null=True, blank=True,
                                   related_name='records_updated')

    sources = models.ManyToManyField('self', blank=True)

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

    def human(self):
        return self.indicator.format_value(value=self.value,
                                           numerator=self.numerator,
                                           denominator=self.denominator)

    def __str__(self):
        return "{i}@{p}".format(i=self.indicator, p=self.period)

    def __unicode__(self):
        return self.__str__()

    def record_update(self, partner):
        self.updated_on = timezone.now()
        self.updated_by = partner
        self.save()

    @classmethod
    def get_or_none(cls, indicator, period, entity):
        try:
            return cls.objects.get(indicator=indicator,
                                   period=period, entity=entity)
        except cls.DoesNotExist:
            return None

    @classmethod
    def batch_create(cls, data, partner):
        if not isinstance(data['meta']['period'], MonthPeriod):
            raise ValueError("Incorrect period")
        if not isinstance(data['meta']['entity'], Entity):
            raise ValueError("Incorrect entity")

        for slug, dp in data.items():
            if slug == 'meta':
                continue

            indic = Indicator.get_or_none(slug)
            dr = cls.get_or_none(indicator=indic,
                                 period=data['meta']['period'],
                                 entity=data['meta']['entity'])

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
                    period=data['meta']['period'],
                    entity=data['meta']['entity'],
                    numerator=num,
                    denominator=denum,
                    source=cls.UPLOAD,
                    created_by=partner)
            else:
                # new data are identical to datarecord
                continue

            data[slug].update({
                'action': action,
                'id': dr.id,
                'previous': old_values})

        return data


class Metadata(models.Model):

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
