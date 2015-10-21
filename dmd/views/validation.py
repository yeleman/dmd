#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging

from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

logger = logging.getLogger(__name__)


class ValidationForm(forms.Form):
    pass


@login_required
@user_passes_test(lambda u: u.partner.can_validate)
def validation(request, template_name='validation.html'):

    context = {'page': 'validation'}

    if request.method == 'POST':
        form = ValidationForm(request.POST, request.FILES)
        if form.is_valid():
            pass
        else:
            # django form validation errors
            pass
    else:
        form = ValidationForm()

    context.update({'form': form})

    return render(request, template_name, context)
