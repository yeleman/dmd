#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class Organization(models.Model):

    class Meta:
        app_label = 'dmd'

    slug = models.SlugField(max_length=96, primary_key=True)
    name = models.CharField(max_length=256)

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


class Partner(models.Model):

    class Meta:
        app_label = 'dmd'
        ordering = ['user__last_name', 'user__first_name']

    user = models.OneToOneField(User)
    organization = models.ForeignKey(Organization,
                                     verbose_name=_("Organization"),
                                     related_name='partners')

    can_upload = models.BooleanField(default=False,
                                     verbose_name=_("Can Upload?"))
    upload_location = models.ForeignKey('Entity', null=True, blank=True,
                                        verbose_name=_("Upload location"),
                                        related_name='upload_partners')

    can_validate = models.BooleanField(default=False,
                                       verbose_name=_("Can Validate?"))
    validation_location = models.ForeignKey(
        'Entity', null=True, blank=True, verbose_name=_("Validation location"),
        related_name='validation_partners')

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

    @classmethod
    def validation_bot(cls):
        return cls.objects.get(user__username='validation_bot')

    def with_org(self):
        if not self.organization:
            return str(self.user)
        return "{user}/{org}".format(user=str(self.user),
                                     org=str(self.organization))
