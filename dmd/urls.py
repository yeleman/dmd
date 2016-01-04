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
        {'next_page': '/' + uprefix}, name='logout'),

    # Entities API
    url(r'^' + uprefix + 'api/entities/getchildren/'
        '(?P<parent_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.api.get_entity_children',
        name='api_entities_get_children'),
    url(r'^' + uprefix + 'api/entities/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.api.get_entity_detail',
        name='api_entity_detail'),

    url(r'^' + uprefix + 'api/geojson/children/'
        '(?P<parent_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.api.children_geojson',
        name='api_entity_children_geojson'),

    url(r'^' + uprefix + 'api/geojson/single/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.api.single_geojson',
        name='api_entity_geojson'),

    url(r'^' + uprefix + 'api/indicators/'
        '(?P<col_type>[A-Za-z]+)/?$',
        'dmd.views.api.indicator_list',
        name='api_indicators_list'),

    url(r'^' + uprefix + 'api/data_record/'
        '(?P<period_str>[0-9]{4}\-[0-9]{2})/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/'
        '(?P<indicator_slug>[A-Za-z0-9\-\_]+)/?$',
        'dmd.views.api.json_data_record_for',
        name='api_data_record_for'),

    # home
    url(r'^' + uprefix + '/?$', 'dmd.views.misc.home', name='home'),

    # partner public profile
    url(r'^' + uprefix + '~(?P<username>[a-zA-Z0-9\@\.\+\-\_]{1,30})/?$',
        'dmd.views.misc.user_profile', name='user_profile'),

    # partner's own password change
    url(r'^' + uprefix + 'change_password/$',
        'dmd.views.misc.user_change_password', name='user_change_password'),

    # upload
    url(r'^' + uprefix + 'upload/guide/?$', 'dmd.views.upload.upload_guide',
        name='upload_guide'),
    url(r'^' + uprefix + 'upload/guide/(?P<uuid>[A-Za-z0-9\_\-]{36})/?$',
        'dmd.views.upload.upload_guide_download',
        name='upload_guide_download'),
    url(r'^' + uprefix + 'upload/?$', 'dmd.views.upload.upload',
        name='upload'),

    # validation
    url(r'^' + uprefix + 'validation/?$', 'dmd.views.validation.validation',
        name='validation'),

    # raw data
    url(r'^' + uprefix + 'raw_data/record/(?P<record_id>[0-9]+)/?$',
        'dmd.views.raw_data.raw_data_record', name='raw_data_record'),
    url(r'^' + uprefix + 'raw_data/record/(?P<record_id>[0-9]+)/noframe/?$',
        'dmd.views.raw_data.raw_data_record',
        {'template_name': 'raw_data_record_noframe.html'},
        name='raw_data_record_noframe'),

    url(r'^' + uprefix + 'raw_data/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<period_str>[0-9]{4}\-[0-9]{2})/?$',
        'dmd.views.raw_data.raw_data', name='raw_data'),
    url(r'^' + uprefix + 'raw_data/(?P<entity_uuid>[a-z\-0-9]{36})/?$',
        'dmd.views.raw_data.raw_data', name='raw_data'),
    url(r'^' + uprefix + 'raw_data/?$', 'dmd.views.raw_data.raw_data',
        name='raw_data'),

    # export
    url(r'^' + uprefix + 'exported/(?P<fpath>.*)/?$',
        'dmd.views.misc.serve_exported_files', name='exported_files'),
    url(r'^' + uprefix + 'export/?$', 'dmd.views.raw_data.data_export',
        name='export'),

    # map
    url(r'^' + uprefix + 'analysis/map/png/initial.png$',
        'dmd.views.api.png_map_for',
        {'period_str': None,
         'entity_uuid': '9616cf8b-5c47-49e2-8702-4f8179565a0c',
         'indicator_slug': None},
        name='png_map'),
    url(r'^' + uprefix + 'analysis/map/png/'
        r'(?P<period_str>[0-9]{4}\-[0-9]{2})_'
        r'(?P<entity_uuid>[A-Za-z0-9\_\-]{36})_'
        r'(?P<indicator_slug>[A-Za-z0-9\-\_]+).png$',
        'dmd.views.api.png_map_for', name='png_map'),
    url(r'^' + uprefix + 'analysis/map/?$', 'dmd.views.analysis.map',
        name='map'),

    # section 1
    url(r'^' + uprefix + 'analysis/section1'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<perioda_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<periodb_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<indicator_slug>[A-Za-z0-9\-\_]+)/?$',
        'dmd.analysis.section1.view', name='section1'),
    url(r'^' + uprefix + 'analysis/section1'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<perioda_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<periodb_str>[0-9]{4}\-[0-9]{2})'
        r'/?$',
        'dmd.analysis.section1.view', name='section1'),
    url(r'^' + uprefix + 'analysis/section1'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/?$',
        'dmd.analysis.section1.view', name='section1'),
    url(r'^' + uprefix + 'analysis/section1'
        r'/?$',
        'dmd.analysis.section1.view', name='section1'),

    # generic analysis
    url(r'^' + uprefix + 'analysis/section(?P<section_id>[0-9]+)'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<perioda_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<periodb_str>[0-9]{4}\-[0-9]{2})'
        r'/?$',
        'dmd.views.analysis.analysis', name='analysis'),
    url(r'^' + uprefix + 'analysis/section(?P<section_id>[0-9]+)/?$',
        'dmd.views.analysis.analysis', name='analysis'),
    url(r'^' + uprefix + 'analysis/?$', 'dmd.views.analysis.analysis',
        name='analysis'),

    # users
    url(r'^' + uprefix + 'users/add/?$',
        'dmd.views.admin.user_add', name='user_add'),
    url(r'^' + uprefix + 'users/(?P<username>[a-zA-Z0-9\-\_]+)/reset?$',
        'dmd.views.admin.user_passwd_reset', name='user_passwd_reset'),
    url(r'^' + uprefix + 'users/(?P<username>[a-zA-Z0-9\-\_]+)/?$',
        'dmd.views.admin.user_edit', name='user_edit'),
    url(r'^' + uprefix + 'users/?$', 'dmd.views.admin.users_list',
        name='users'),

    # indicators
    url(r'^' + uprefix + 'indicators/download/?$',
        'dmd.views.misc.indicators_list_as_excel', name='indicators_xlsx'),
    url(r'^' + uprefix + 'indicators/add/?$',
        'dmd.views.admin.indicator_add', name='indicator_add'),
    url(r'^' + uprefix + 'indicators/(?P<slug>[a-zA-Z0-9\-\_]+)/?$',
        'dmd.views.admin.indicator_edit', name='indicator_edit'),
    url(r'^' + uprefix + 'indicators/?$',
        'dmd.views.misc.indicators_list', name='indicators'),

    # organizations
    url(r'^' + uprefix + 'organizations/add/?$',
        'dmd.views.admin.organization_add', name='organization_add'),
    url(r'^' + uprefix + 'organizations/(?P<slug>[a-zA-Z0-9\-\_]+)/?$',
        'dmd.views.admin.organization_edit', name='organization_edit'),
    url(r'^' + uprefix + 'organizations/?$',
        'dmd.views.admin.organizations_list', name='organizations'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
