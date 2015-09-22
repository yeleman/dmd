#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),

    # authentication
    url(r'^login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'}, name='logout'),

    # Entities API
    url(r'^api/entities/getchildren/'
        '(?P<parent_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.get_entity_children',
        name='api_entities_get_children'),
    url(r'^api/entities/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.get_entity_detail',
        name='api_entity_detail'),

    url(r'^/?$', 'dmd.views.home', name='home'),
    url(r'^upload/step2/?$', 'dmd.views.upload_step2', name='upload_step2'),
    url(r'^upload/?$', 'dmd.views.upload', name='upload'),
    url(r'^raw_data/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<period_str>[0-9]{4}\-[0-9]{2})/?$',
        'dmd.views.raw_data', name='raw_data'),
    url(r'^raw_data/(?P<entity_uuid>[a-z\-0-9]{36})/?$',
        'dmd.views.raw_data', name='raw_data'),
    url(r'^raw_data/?$', 'dmd.views.raw_data', name='raw_data'),
    url(r'^export/?$', 'dmd.views.data_export', name='export'),
    url(r'^analysis/?$', 'dmd.views.analysis', name='analysis'),
    url(r'^users/?$', 'dmd.views.users_list', name='users'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
