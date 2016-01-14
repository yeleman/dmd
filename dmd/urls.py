#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from __future__ import (unicode_literals, absolute_import,
                        division, print_function)

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.views import (
    login as login_view, logout as logout_view)

from dmd.views import api as api_views
from dmd.views import admin as admin_views
from dmd.views import misc as misc_views
from dmd.views import raw_data as raw_data_views
from dmd.views import analysis as analysis_views
from dmd.views import upload as upload_views
from dmd.views import validation as validation_views
from dmd.analysis import section1, section2

uprefix = settings.SUB_PATH if settings.SUB_PATH else r''

urlpatterns = [
    url(r'^' + uprefix + 'admin/', include(admin.site.urls)),

    # authentication
    url(r'^' + uprefix + 'login/$', login_view,
        {'template_name': 'login.html'}, name='login'),
    url(r'^' + uprefix + 'logout/$', logout_view,
        {'next_page': '/' + uprefix}, name='logout'),

    # Entities API
    url(r'^' + uprefix + 'api/entities/getchildren/'
        '(?P<parent_uuid>[A-Za-z0-9\_\-]{36})/?$',
        api_views.get_entity_children,
        name='api_entities_get_children'),
    url(r'^' + uprefix + 'api/entities/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/?$',
        api_views.get_entity_detail,
        name='api_entity_detail'),

    url(r'^' + uprefix + 'api/geojson/children/'
        '(?P<parent_uuid>[A-Za-z0-9\_\-]{36})/?$',
        api_views.children_geojson,
        name='api_entity_children_geojson'),

    url(r'^' + uprefix + 'api/geojson/single/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/?$',
        api_views.single_geojson,
        name='api_entity_geojson'),

    url(r'^' + uprefix + 'api/indicators/'
        '(?P<col_type>[A-Za-z]+)/?$',
        api_views.indicator_list,
        name='api_indicators_list'),

    url(r'^' + uprefix + 'api/data_record/'
        '(?P<period_str>[0-9]{4}\-[0-9]{2})/'
        '(?P<entity_uuid>[A-Za-z0-9\_\-]{36})/'
        '(?P<indicator_slug>[A-Za-z0-9\-\_]+)/?$',
        api_views.json_data_record_for,
        name='api_data_record_for'),

    # home
    url(r'^' + uprefix + '$', misc_views.home, name='home'),

    url(r'^' + uprefix + 'dashboard'
        r'/(?P<period_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<indicator_slug>[A-Za-z0-9\-\_]+)/?$',
        analysis_views.dashboard,
        name='dashboard'),
    url(r'^' + uprefix + 'dashboard', analysis_views.dashboard,
        name='dashboard'),

    # partner public profile
    url(r'^' + uprefix + '~(?P<username>[a-zA-Z0-9\@\.\+\-\_]{1,30})/?$',
        misc_views.user_profile, name='user_profile'),

    # partner's own password change
    url(r'^' + uprefix + 'change_password/$',
        misc_views.user_change_password, name='user_change_password'),

    # upload
    url(r'^' + uprefix + 'upload/guide/?$', upload_views.upload_guide,
        name='upload_guide'),
    url(r'^' + uprefix + 'upload/guide/(?P<uuid>[A-Za-z0-9\_\-]{36})/?$',
        upload_views.upload_guide_download,
        name='upload_guide_download'),
    url(r'^' + uprefix + 'upload/?$', upload_views.upload,
        name='upload'),

    # validation
    url(r'^' + uprefix + 'validation/?$', validation_views.validation,
        name='validation'),

    # raw data
    url(r'^' + uprefix + 'raw_data/record/(?P<record_id>[0-9]+)/?$',
        raw_data_views.raw_data_record, name='raw_data_record'),
    url(r'^' + uprefix + 'raw_data/record/(?P<record_id>[0-9]+)/noframe/?$',
        raw_data_views.raw_data_record,
        {'template_name': 'raw_data_record_noframe.html'},
        name='raw_data_record_noframe'),

    url(r'^' + uprefix + 'raw_data/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<period_str>[0-9]{4}\-[0-9]{2})/?$',
        raw_data_views.raw_data, name='raw_data'),
    url(r'^' + uprefix + 'raw_data/(?P<entity_uuid>[a-z\-0-9]{36})/?$',
        raw_data_views.raw_data, name='raw_data'),
    url(r'^' + uprefix + 'raw_data/?$', raw_data_views.raw_data,
        name='raw_data'),

    # export
    url(r'^' + uprefix + 'exported/(?P<fpath>.*)/?$',
        misc_views.serve_exported_files, name='exported_files'),
    url(r'^' + uprefix + 'export/?$', raw_data_views.data_export,
        name='export'),

    # map
    url(r'^' + uprefix + 'analysis/map/png/initial.png$',
        api_views.png_map_for,
        {'period_str': None,
         'entity_uuid': '9616cf8b-5c47-49e2-8702-4f8179565a0c',
         'indicator_slug': None},
        name='png_map'),
    url(r'^' + uprefix + 'analysis/map/png/'
        r'(?P<period_str>[0-9]{4}\-[0-9]{2})_'
        r'(?P<entity_uuid>[A-Za-z0-9\_\-]{36})_'
        r'(?P<indicator_slug>[A-Za-z0-9\-\_]+).png$',
        api_views.png_map_for, name='png_map'),
    url(r'^' + uprefix + 'analysis/map/?$', analysis_views.map,
        name='map'),

    # section 1
    url(r'^' + uprefix + 'analysis/section1'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<perioda_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<periodb_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<indicator_slug>[A-Za-z0-9\-\_]+)/?$',
        section1.view, name='section1'),

    # section 2
    url(r'^' + uprefix + 'analysis/section2'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<period_str>[0-9]{4}\-[0-9]{2})/?$',
        section2.view, name='section2'),
    url(r'^' + uprefix + 'analysis/section2/?$',
        section2.view, name='section2'),

    url(r'^' + uprefix + 'analysis/section1'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<perioda_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<periodb_str>[0-9]{4}\-[0-9]{2})'
        r'/?$',
        section1.view, name='section1'),
    url(r'^' + uprefix + 'analysis/section1'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/?$',
        section1.view, name='section1'),
    url(r'^' + uprefix + 'analysis/section1'
        r'/?$',
        section1.view, name='section1'),

    # generic analysis
    url(r'^' + uprefix + 'analysis/section(?P<section_id>[0-9]+)'
        r'/(?P<entity_uuid>[a-z\-0-9]{36})'
        r'/(?P<perioda_str>[0-9]{4}\-[0-9]{2})'
        r'/(?P<periodb_str>[0-9]{4}\-[0-9]{2})'
        r'/?$',
        analysis_views.analysis, name='analysis'),
    url(r'^' + uprefix + 'analysis/section(?P<section_id>[0-9]+)/?$',
        analysis_views.analysis, name='analysis'),
    url(r'^' + uprefix + 'analysis/?$', analysis_views.analysis,
        name='analysis'),

    # users
    url(r'^' + uprefix + 'users/add/?$',
        admin_views.user_add, name='user_add'),
    url(r'^' + uprefix + 'users/(?P<username>[a-zA-Z0-9\-\_]+)/reset?$',
        admin_views.user_passwd_reset, name='user_passwd_reset'),
    url(r'^' + uprefix + 'users/(?P<username>[a-zA-Z0-9\-\_]+)/?$',
        admin_views.user_edit, name='user_edit'),
    url(r'^' + uprefix + 'users/?$', admin_views.users_list,
        name='users'),

    # indicators
    url(r'^' + uprefix + 'indicators/download/?$',
        misc_views.indicators_list_as_excel, name='indicators_xlsx'),
    url(r'^' + uprefix + 'indicators/add/?$',
        admin_views.indicator_add, name='indicator_add'),
    url(r'^' + uprefix + 'indicators/(?P<slug>[a-zA-Z0-9\-\_]+)/?$',
        admin_views.indicator_edit, name='indicator_edit'),
    url(r'^' + uprefix + 'indicators/?$',
        misc_views.indicators_list, name='indicators'),

    # organizations
    url(r'^' + uprefix + 'organizations/add/?$',
        admin_views.organization_add, name='organization_add'),
    url(r'^' + uprefix + 'organizations/(?P<slug>[a-zA-Z0-9\-\_]+)/?$',
        admin_views.organization_edit, name='organization_edit'),
    url(r'^' + uprefix + 'organizations/?$',
        admin_views.organizations_list, name='organizations'),

    # backups
    url(r'^' + uprefix + 'backups/?$',
        admin_views.backups_list, name='backups'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
