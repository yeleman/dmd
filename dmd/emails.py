#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)
import smtplib
import logging
import traceback

from django.core import mail
from django.conf import settings
from django.template import loader, RequestContext
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.http import HttpRequest

logger = logging.getLogger(__name__)


def send_email(recipients, message=None, template=None, context={},
               title=None, title_template=None, sender=None):
    """ forge and send an email message

        recipients: a list of or a string email address
        message: string or template name to build email body
        title: string or title_template to build email subject
        sender: string otherwise EMAIL_SENDER setting
        content: a dict to be used to render both templates

        returns: (success, message)
            success: a boolean if connecion went through
            message: an int number of email sent if success is True
                     else, an Exception """

    if not isinstance(recipients, (list, tuple)):
        recipients = [recipients]

    # remove empty emails from list
    # might happen everytime a user did not set email address.
    try:
        while True:
            recipients.remove("")
    except ValueError:
        pass

    # no need to continue if there's no recipients
    if len(recipients) == 0:
        return (False, ValueError(_("No Recipients for that message")))

    # no body text forbidden. most likely an error
    if not message and not template:
        return (False, ValueError(_("Unable to send empty email messages")))

    # build email body. rendered template has priority
    if template:
        email_msg = loader.get_template(template).render(RequestContext(
            HttpRequest(), context))
    else:
        email_msg = message

    # if no title provided, use default one. empty title allowed
    if title is None and not title_template:
        email_subject = _("Message from {site}").format(
            site=Site.objects.get_current().name)

    # build email subject. rendered template has priority
    if title_template:
        email_subject = loader.get_template(title_template) \
                              .render(RequestContext(HttpRequest(),
                                                     context))
    elif title is not None:
        email_subject = title

    # title can't contain new line
    email_subject = email_subject.strip()

    # default sender from config
    if not sender:
        sender = settings.EMAIL_SENDER

    msgs = []
    for recipient in recipients:
        msgs.append((email_subject, email_msg, sender, [recipient]))

    try:
        mail.send_mass_mail(tuple(msgs), fail_silently=False)
        return (True, recipients.__len__())
    except smtplib.SMTPException as e:
        # log that error
        logger.error("SMTP Exception: %r".format(e))
        logger.debug("".join(traceback.format_exc()))
    except Exception as e:
        logger.error("Exception in sending Email: %r".format(e))
        logger.debug("".join(traceback.format_exc()))
    return (False, e)
