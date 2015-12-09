# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0008_auto_20151125_1210'),
    ]

    operations = [
        migrations.AddField(
            model_name='datarecord',
            name='arrival_status',
            field=models.CharField(default='not_validated', max_length=128, choices=[('late', 'Late'), ('not_arrived', 'Not Arrived'), ('on_time', 'On Time')]),
        ),
        migrations.AddField(
            model_name='indicator',
            name='prompt_transmission_delay',
            field=models.PositiveIntegerField(help_text='In days', null=True, verbose_name='Prompt Transmission Delay', blank=True),
        ),
        migrations.AlterField(
            model_name='datarecord',
            name='source',
            field=models.CharField(max_length=128, choices=[('dhis', 'DHIS'), ('upload', 'Direct'), ('aggregation', 'Aggregation')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='category',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Category', choices=[('process', 'Process'), ('effect', 'Effect')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='collection_level',
            field=models.CharField(max_length=64, verbose_name='Collection Level', choices=[('pays', 'Country'), ('division_provinciale_sante', 'Division Provinciale de la Sant\xe9'), ('zone_sante', 'Zone de sant\xe9')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='collection_period',
            field=models.PositiveIntegerField(help_text='In months', verbose_name='Collection Periodicity'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='collection_type',
            field=models.CharField(max_length=64, verbose_name='Collection Type', choices=[('survey', 'Survey'), ('routine', 'Routine')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='dhis_denominator_formula',
            field=models.CharField(help_text='For reference only', max_length=512, null=True, verbose_name='DHIS Denominator Formula', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='dhis_denominator_id',
            field=models.CharField(help_text='Mandatory for DHIS Indicator', max_length=64, null=True, verbose_name='DHIS Denominator ID', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='dhis_indicator_id',
            field=models.CharField(help_text='For reference only', max_length=64, null=True, verbose_name='DHIS Indicator ID', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='dhis_numerator_formula',
            field=models.CharField(help_text='For reference only', max_length=512, null=True, verbose_name='DHIS Numerator Formula', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='dhis_numerator_id',
            field=models.CharField(help_text='Mandatory for DHIS Indicator', max_length=64, null=True, verbose_name='DHIS Numerator ID', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='itype',
            field=models.CharField(max_length=64, verbose_name='Indicator Type', choices=[('per_thousand', 'Per 1,000'), ('per_hundred_thousand', 'Per 100,000'), ('per_ten_thousand', 'Per 10,000'), ('proportion', 'Proportion'), ('number', 'Number'), ('percentage', 'Percentage')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='name',
            field=models.CharField(max_length=512, verbose_name='French name'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='name_en',
            field=models.CharField(max_length=512, null=True, verbose_name='English name', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='number',
            field=models.CharField(help_text='Respect convention', unique=True, max_length=8, verbose_name='Indicator number'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='number_format',
            field=models.CharField(max_length=32, verbose_name='Number Format', choices=[('#,##0;-#', 'Integer'), ('#,##0.##;-#', 'Float, precision 2'), ('#,##0.#;-#', 'Float, precision 1')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='organizations',
            field=models.ManyToManyField(related_name='indicators', verbose_name='Organizations', to='dmd.Organization', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='origin',
            field=models.CharField(help_text='Careful with DHIS indicators', max_length=64, verbose_name='origin', choices=[('dhis', 'DHIS'), ('manual', 'Manual')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='slug',
            field=models.SlugField(primary_key=True, serialize=False, max_length=255, help_text='Lowercase english summary without spaces', verbose_name='Identifier'),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='tech_area1',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Tech Area 1', choices=[('hss', 'Health System Strengthening'), ('pvc', 'Prevention Vector Control'), ('sme', 'Surveillance and M&E'), ('cm', 'Case Management'), ('bcc', 'Behavioral Chance Communication')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='tech_area2',
            field=models.CharField(blank=True, max_length=64, null=True, verbose_name='Tech Area 2', choices=[('capacity_building', 'Capacity building'), ('itn/llin', 'ITN/LLIN'), ('psm', 'PSM'), ('iptp', 'IPTp'), ('enable_environment', 'Enable environment'), ('knowledge', 'Knowledge'), ('irs', 'IRS'), ('supervision', 'Supervision'), ('treatment', 'Treatment'), ('diagnosis', 'Diagnosis'), ('community_case_management', 'Community Case Management')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='transmission_delay',
            field=models.PositiveIntegerField(help_text='In days', null=True, verbose_name='Transmission Delay', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='transmission_organizations',
            field=models.ManyToManyField(related_name='transmission_indicators', verbose_name='Transmitting Organizations', to='dmd.Organization', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='validation_delay',
            field=models.PositiveIntegerField(help_text='In days', null=True, verbose_name='Validation Delay', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='validation_organizations',
            field=models.ManyToManyField(related_name='validation_indicators', verbose_name='Validating Organizations', to='dmd.Organization', blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='value_format',
            field=models.CharField(max_length=64, verbose_name='Value Format', choices=[('{numerator}/{denominator}', 'a/b'), ('{value}%', 'x%'), ('{value}/1\xa0000', 'x/1000'), ('{value}/100\xa0000', 'x/100 000'), ('{value}/10\xa0000', 'x/10 000'), ('{value}', 'x')]),
        ),
    ]
