#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

uprefix = settings.SUB_PATH if settings.SUB_PATH else r''

urlpatterns = [
    url(r'^' + uprefix + 'admin/', include(admin.site.urls)),

    # authentication
    url(r'^' + uprefix + 'login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, name='login'),
    url(r'^' + uprefix + 'logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/' + uprefix + '/'}, name='logout'),

    # Entities API
    url(r'^' + uprefix + 'api/entities/getchildren/'
        '(?P<parent_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.get_entity_children',
        name='api_entities_get_children'),
    url(r'^' + uprefix + 'api/entities/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.get_entity_detail',
        name='api_entity_detail'),

    # home
    url(r'^' + uprefix + '/?$', 'dmd.views.home', name='home'),

    # visitor profile
    url(r'^' + uprefix + 'change_password/$',
        'dmd.views.user_change_password', name='user_change_password'),

    # upload
    url(r'^' + uprefix + 'upload/step2/?$', 'dmd.views.upload_step2',
        name='upload_step2'),
    url(r'^' + uprefix + 'upload/?$', 'dmd.views.upload', name='upload'),

    # raw data
    url(r'^' + uprefix + 'raw_data/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<period_str>[0-9]{4}\-[0-9]{2})/?$',
        'dmd.views.raw_data', name='raw_data'),
    url(r'^' + uprefix + 'raw_data/(?P<entity_uuid>[a-z\-0-9]{36})/?$',
        'dmd.views.raw_data', name='raw_data'),
    url(r'^' + uprefix + 'raw_data/?$', 'dmd.views.raw_data', name='raw_data'),

    # export
    url(r'^exported/(?P<fpath>.*)/?$',
        'dmd.views.serve_exported_files', name='exported_files'),
    url(r'^' + uprefix + 'export/?$', 'dmd.views.data_export', name='export'),

    # analysis
    url(r'^' + uprefix + 'analysis/?$', 'dmd.views.analysis', name='analysis'),

    # users
    url(r'^' + uprefix + 'users/add/?$',
        'dmd.views.user_add', name='user_add'),
    url(r'^' + uprefix + 'users/(?P<username>[a-zA-Z0-9\-\_]+)/reset?$',
        'dmd.views.user_passwd_reset', name='user_passwd_reset'),
    url(r'^' + uprefix + 'users/(?P<username>[a-zA-Z0-9\-\_]+)/?$',
        'dmd.views.user_edit', name='user_edit'),
    url(r'^' + uprefix + 'users/?$', 'dmd.views.users_list', name='users'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
