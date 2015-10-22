#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import logging
import tempfile
import os

from py3compat import text_type
from django.http import HttpResponse, Http404
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy
from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from dmd.models import Entity, DataRecord
from dmd.xlsx.xlimport import (read_xls, ExcelValueMissing,
                               ExcelValueError, IncorrectExcelFile)
from dmd.xlsx.xlexport import dataentry_fname_for, generate_dataentry_for

logger = logging.getLogger(__name__)


def handle_uploaded_file(f):
    """ stores temporary file as a real file for form upload """
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    for chunk in f.chunks():
        tfile.write(chunk)
    tfile.close()
    return tfile.name


class ExcelUploadForm(forms.Form):
    data_file = forms.FileField(label=ugettext_lazy("Report File"))


def create_records_from(request, xls_data, filepath=None):
    redir = False
    try:
        payload = DataRecord.batch_create(xls_data,
                                          request.user.partner)
    except Exception as e:
        logger.exception(e)
        messages.error(request, text_type(e))
    else:
        nb_created = sum([1 for v in payload.values()
                          if v.get('action') == 'created'])
        nb_updated = sum([1 for v in payload.values()
                          if v.get('action') == 'updated'])
        if nb_created or nb_updated:
            message = _("Congratulations! Your data has been recorded.")
            if nb_created:
                message += "\n" + _("{nb_created} records were created.")
            if nb_updated:
                message += "\n" + _("{nb_updated} records were updated.")
            messages.success(request, message.format(nb_created=nb_created,
                                                     nb_updated=nb_updated))
        else:
            messages.info(request, _("Thank You for submitting! "
                                     "No new data to record though."))
        redir = True
    finally:
        if filepath is not None:
            os.unlink(filepath)
    return redir


@login_required
def upload(request, template_name='upload.html'):

    context = {'page': 'upload'}

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            filepath = handle_uploaded_file(request.FILES['data_file'])

            try:
                xls_data = read_xls(filepath)
            except Exception as e:
                logger.exception(e)
                if isinstance(e, (IncorrectExcelFile,
                                  ExcelValueMissing,
                                  ExcelValueError)):
                    messages.error(request, text_type(e))
                else:
                    messages.error(
                        request, _("Unexpected Error while reading XLS file"))
                return redirect('upload')

            if create_records_from(request, xls_data, filepath):
                return redirect('upload')
        else:
            # django form validation errors
            pass
    else:
        form = ExcelUploadForm()

    context.update({'form': form})

    return render(request, template_name, context)


def upload_guide(request, *args, **kwargs):
    context = {'page': 'upload'}

    context.update({
        'provinces': Entity.get_root().get_children(),
    })
    return render(request,
                  kwargs.get('template_name', 'upload_guide.html'),
                  context)


def upload_guide_download(request, uuid, *args, **kwargs):

    dps = Entity.get_or_none(uuid)
    if dps is None:
        return Http404(_("No Entity to match `{uuid}`").format(uuid=uuid))

    file_name = dataentry_fname_for(dps)
    file_content = generate_dataentry_for(dps).getvalue()

    response = HttpResponse(file_content,
                            content_type='application/'
                                         'vnd.openxmlformats-officedocument'
                                         '.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
    response['Content-Length'] = len(file_content)

    return response
