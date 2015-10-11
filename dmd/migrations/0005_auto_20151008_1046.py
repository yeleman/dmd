# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0004_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarecord',
            name='validated_by',
            field=models.ForeignKey(related_name='records_validated', blank=True, to='dmd.Partner', null=True),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='validated_on',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='datarecord',
            name='validation_status',
            field=models.CharField(default='not_validated', max_length=128, choices=[('validated', 'Validated'), ('auto_validated', 'Auto Validated'), ('not_validated', 'Not Validated'), ('rejected', 'Rejected'), ('modified', 'Modified')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='indicator',
            name='collection_level',
            field=models.CharField(default='division_provinciale_sante', max_length=64, choices=[('pays', 'Country'), ('division_provinciale_sante', 'Division Provinciale de la Sant\xe9'), ('zone_sante', 'Zone de sant\xe9'), ('aire_sante', 'Aire de Sant\xe9')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='indicator',
            name='collection_period',
            field=models.PositiveIntegerField(default=1, help_text='In months'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='indicator',
            name='collection_type',
            field=models.CharField(default='survey', max_length=64, choices=[('survey', 'Survey'), ('routine', 'Routine')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='indicator',
            name='transmission_delay',
            field=models.PositiveIntegerField(help_text='In days', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='indicator',
            name='transmission_organizations',
            field=models.ManyToManyField(related_name='transmission_indicators', to='dmd.Organization', blank=True),
        ),
        migrations.AddField(
            model_name='indicator',
            name='validation_delay',
            field=models.PositiveIntegerField(help_text='In days', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='indicator',
            name='validation_organizations',
            field=models.ManyToManyField(related_name='validation_indicators', to='dmd.Organization', blank=True),
        ),
        migrations.AddField(
            model_name='partner',
            name='can_validate',
            field=models.BooleanField(default=False, verbose_name='Can Upload?'),
        ),
        migrations.AddField(
            model_name='partner',
            name='validation_location',
            field=models.ForeignKey(related_name='validation_partners', verbose_name='Validation location', blank=True, to='dmd.Entity', null=True),
        ),
        migrations.AlterField(
            model_name='entity',
            name='etype',
            field=models.CharField(max_length=64, choices=[('pays', 'Country'), ('division_provinciale_sante', 'Division Provinciale de la Sant\xe9'), ('zone_sante', 'Zone de sant\xe9'), ('aire_sante', 'Aire de Sant\xe9')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='category',
            field=models.CharField(blank=True, max_length=64, null=True, choices=[('process', 'Process'), ('effect', 'Effect')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='itype',
            field=models.CharField(max_length=64, choices=[('per_thousand', 'Per 1,000'), ('per_hundred_thousand', 'Per 100,000'), ('per_ten_thousand', 'Per 10,000'), ('proportion', 'Proportion'), ('number', 'Number'), ('percentage', 'Percentage')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='number_format',
            field=models.CharField(max_length=32, choices=[('{:.0f}', 'Integer'), ('{:.2f}', 'Float, precision 2'), ('{:.1f}', 'Float, precision 1')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='organizations',
            field=models.ManyToManyField(related_name='indicators', to='dmd.Organization', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='origin',
            field=models.CharField(max_length=64, choices=[('dhis', 'DHIS'), ('manual', 'Manual')]),
        ),
        migrations.AlterField(
            model_name='partner',
            name='can_upload',
            field=models.BooleanField(default=False, verbose_name='Can Upload?'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='organization',
            field=models.ForeignKey(related_name='partners', verbose_name='Organization', to='dmd.Organization'),
        ),
        migrations.AlterField(
            model_name='partner',
            name='upload_location',
            field=models.ForeignKey(related_name='upload_partners', verbose_name='Upload location', blank=True, to='dmd.Entity', null=True),
        ),
    ]
