#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import collections

from django import forms
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import ugettext as _

from dmd.models.DataRecords import DataRecord
from dmd.models.Entities import Entity
from dmd.models.Periods import MonthPeriod
from dmd.xlsx.xlexport import (generate_validation_tally_for,
                               validation_tallysheet_fname_for)
from dmd.views.common import process_period_filter

MAX_RESULTS = 50
MAX_MONTHS = 4

logger = logging.getLogger(__name__)


class ValidationForm(forms.Form):

    WAIT = DataRecord.NOT_VALIDATED
    VALIDATED = DataRecord.VALIDATED
    REJECTED = DataRecord.REJECTED
    EDIT = 'edit'

    STATUSES = collections.OrderedDict([
        (WAIT, _("Wait")),
        (VALIDATED, DataRecord.VALIDATION_STATUSES.get(VALIDATED)),
        (REJECTED, DataRecord.VALIDATION_STATUSES.get(REJECTED)),
        (EDIT, _("Edit")),
    ])

    def __init__(self, *args, **kwargs):
        records = kwargs.pop('records')
        super(ValidationForm, self).__init__(*args, **kwargs)

        self.fields = collections.OrderedDict([])

        for record in records:
            label = "{p}/{l}: {i}".format(
                p=record.period.strid, l=record.entity,
                i=record.indicator.name)
            status_key = 'status-{}'.format(record.id)
            numerator_key = 'numerator-{}'.format(record.id)
            denominator_key = 'denominator-{}'.format(record.id)
            self.fields.update({
                status_key: forms.ChoiceField(
                    label=label,
                    choices=self.STATUSES.items(),
                    initial=self.initial.get(status_key, self.WAIT)),
            })
            self.fields.update({
                numerator_key: forms.FloatField(
                    min_value=0,
                    label=_("Numerator"),
                    initial=self.initial.get(numerator_key, record.numerator)),
            })
            self.fields.update({
                denominator_key: forms.FloatField(
                    min_value=0,
                    label=_("Denominator"),
                    initial=self.initial.get(denominator_key,
                                             record.denominator)),
            })

        for key in self.fields.keys():
            self.fields[key].widget.attrs['class'] = "form-control"


@login_required
@user_passes_test(lambda u: u.partner.can_validate)
def validation(request, template_name='validation.html'):

    context = {'page': 'validation'}

    # recent periods for tally suggestion
    recent_periods = [MonthPeriod.current().previous()]
    for __ in range(2):
        recent_periods.append(recent_periods[-1].previous())
    context.update({'recent_periods': recent_periods})

    now = timezone.now()
    rdc = Entity.get_root()
    validation_location = request.user.partner.validation_location

    records = DataRecord.objects \
        .filter(validation_status=DataRecord.NOT_VALIDATED)

    if validation_location != rdc:
        other_dps = list(rdc.get_children())
        other_dps.remove(validation_location)
        records = records.exclude(entity__in=other_dps) \
                         .exclude(entity__parent__in=other_dps)
    # set order
    records = records.order_by('-created_on')

    nb_total = records.count()
    records = records[:MAX_RESULTS]

    if request.method == 'POST':
        form = ValidationForm(request.POST, records=records)
        if form.is_valid():
            counts = {
                'untouched': 0,
                'updated': 0,
                'validated': 0,
                'rejected': 0
            }

            for dr in records:
                status = form.cleaned_data.get('status-{}'.format(dr.id))
                if status == form.WAIT:
                    counts['untouched'] += 1
                    continue

                if status == 'edit':
                    numerator = form.cleaned_data.get('numerator-{}'
                                                      .format(dr.id))
                    denominator = form.cleaned_data.get('denominator-{}'
                                                        .format(dr.id))

                    dr.numerator = numerator
                    dr.denominator = denominator
                    dr.record_update(request.user.partner)

                    counts['updated'] += 1

                    status = form.VALIDATED

                if status in (form.VALIDATED, form.REJECTED):
                    if status == form.VALIDATED:
                        counts['validated'] += 1
                    else:
                        counts['rejected'] += 1

                    dr.record_validation(
                        status=status,
                        on=now,
                        by=request.user.partner)
            messages.info(request, _(
                "Thank You for your validations. {w} data were left "
                "untouched, {u} were updated, {v} validated "
                "and {r} rejected.").format(
                    w=counts['untouched'],
                    u=counts['updated'],
                    v=counts['validated'],
                    r=counts['rejected']))

            return redirect('validation')
        else:
            # django form validation errors
            pass
    else:
        form = ValidationForm(records=records)

    context.update({
        'form': form,
        'records': records,
        'nb_total': nb_total
    })

    return render(request, template_name, context)


def validation_tallysheet_download(request, period_str=None, *args, **kwargs):
    context = {}
    dps = request.user.partner.validation_location
    context.update(process_period_filter(request, period_str))
    period = context.get('period') or MonthPeriod.current().previous()

    file_name = validation_tallysheet_fname_for(dps, period)
    file_content = generate_validation_tally_for(dps, period).getvalue()

    response = HttpResponse(file_content,
                            content_type='application/'
                                         'vnd.openxmlformats-officedocument'
                                         '.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
    response['Content-Length'] = len(file_content)

    return response
