# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DataRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numerator', models.FloatField()),
                ('denominator', models.FloatField()),
                ('source', models.CharField(max_length=128, choices=[('dhis', 'DHIS'), ('upload', 'Directe'), ('aggregation', 'Aggregation')])),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('code', models.CharField(max_length=16, unique=True, null=True, blank=True)),
                ('name', models.CharField(max_length=256)),
                ('short_name', models.CharField(max_length=128)),
                ('display_name', models.CharField(max_length=256)),
                ('dhis_level', models.PositiveIntegerField()),
                ('dhis_id', models.CharField(unique=True, max_length=64)),
                ('etype', models.CharField(max_length=64, choices=[('pays', 'Pays'), ('division_provinciale_sante', 'Division Provinciale de la Sant\xe9'), ('zone_sante', 'Zone de sant\xe9'), ('aire_sante', 'Aire de Sant\xe9')])),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='dmd.Entity', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Indicator',
            fields=[
                ('slug', models.SlugField(max_length=256, serialize=False, primary_key=True)),
                ('origin', models.CharField(max_length=64, choices=[('dhis', 'DHIS'), ('manual', 'Manuelle')])),
                ('number', models.CharField(unique=True, max_length=8)),
                ('name', models.CharField(max_length=512)),
                ('name_en', models.CharField(max_length=512, null=True, blank=True)),
                ('dhis_numerator_id', models.CharField(max_length=64, null=True, blank=True)),
                ('dhis_denominator_id', models.CharField(max_length=64, null=True, blank=True)),
                ('category', models.CharField(blank=True, max_length=64, null=True, choices=[('process', 'Processus'), ('effect', 'Effet')])),
                ('tech_area1', models.CharField(blank=True, max_length=64, null=True, choices=[('hss', 'Health System Strengthening'), ('pvc', 'Prevention Vector Control'), ('sme', 'Surveillance and M&E'), ('cm', 'Case Management'), ('bcc', 'Behavioral Chance Communication')])),
                ('tech_area2', models.CharField(blank=True, max_length=64, null=True, choices=[('capacity_building', 'Capacity building'), ('itn/llin', 'ITN/LLIN'), ('psm', 'PSM'), ('iptp', 'IPTp'), ('enable_environment', 'Enable environment'), ('knowledge', 'Knowledge'), ('irs', 'IRS'), ('supervision', 'Supervision'), ('treatment', 'Treatment'), ('diagnosis', 'Diagnosis'), ('community_case_management', 'Community Case Management')])),
                ('itype', models.CharField(max_length=64, choices=[('per_thousand', 'Pour 1000'), ('per_hundred_thousand', 'Pour 100 000'), ('per_ten_thousand', 'Pour 10\xa0000'), ('proportion', 'Proportion'), ('number', 'Nombre'), ('percentage', 'Pourcentage')])),
                ('number_format', models.CharField(max_length=32, choices=[('{:0.2f}', 'R\xe9el deux d\xe9cimales'), ('{:0.1f}', 'R\xe9el une d\xe9cimale'), ('{:0f}', 'Entier')])),
                ('value_format', models.CharField(max_length=64, choices=[('{value}/100\xa0000', 'x/100 000'), ('{value}%', 'x%'), ('{value}', 'x'), ('{value}/1\xa0000', 'x/1000'), ('{value}/10\xa0000', 'x/10 000')])),
            ],
            options={
                'ordering': ['number', 'name'],
            },
        ),
        migrations.CreateModel(
            name='MonthPeriod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('year', models.CharField(max_length=4, choices=[(b'2014', b'2014'), (b'2015', b'2015'), (b'2016', b'2016'), (b'2017', b'2017'), (b'2018', b'2018'), (b'2019', b'2019'), (b'2020', b'2020'), (b'2021', b'2021'), (b'2022', b'2022'), (b'2023', b'2023'), (b'2024', b'2024')])),
                ('month', models.CharField(max_length=2, choices=[(b'01', b'01'), (b'02', b'02'), (b'03', b'03'), (b'04', b'04'), (b'05', b'05'), (b'06', b'06'), (b'07', b'07'), (b'08', b'08'), (b'09', b'09'), (b'10', b'10'), (b'11', b'11'), (b'12', b'12')])),
            ],
            options={
                'ordering': ['year', 'month'],
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('slug', models.SlugField(max_length=96, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('can_upload', models.BooleanField(default=False)),
                ('organization', models.ForeignKey(blank=True, to='dmd.Organization', null=True)),
                ('upload_location', models.ForeignKey(blank=True, to='dmd.Entity', null=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='monthperiod',
            unique_together=set([('year', 'month')]),
        ),
        migrations.AddField(
            model_name='indicator',
            name='organizations',
            field=models.ManyToManyField(to='dmd.Organization', blank=True),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='created_by',
            field=models.ForeignKey(related_name='records_created', to='dmd.Partner'),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='entity',
            field=models.ForeignKey(related_name='data_records', to='dmd.Entity'),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='indicator',
            field=models.ForeignKey(related_name='data_records', to='dmd.Indicator'),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='period',
            field=models.ForeignKey(related_name='data_records', to='dmd.MonthPeriod'),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='sources',
            field=models.ManyToManyField(related_name='sources_rel_+', to='dmd.DataRecord', blank=True),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='updated_by',
            field=models.ForeignKey(related_name='records_updated', blank=True, to='dmd.Partner', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='datarecord',
            unique_together=set([('indicator', 'period', 'entity')]),
        ),
    ]
