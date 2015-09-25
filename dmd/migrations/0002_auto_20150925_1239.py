# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='dhis_denominator_formula',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='indicator',
            name='dhis_indicator_id',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='indicator',
            name='dhis_numerator_formula',
            field=models.CharField(max_length=512, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='value_format',
            field=models.CharField(max_length=64, choices=[('{numerator}/{denominator}', 'a/b'), ('{value}%', 'x%'), ('{value}/1\xa0000', 'x/1000'), ('{value}/100\xa0000', 'x/100 000'), ('{value}/10\xa0000', 'x/10 000'), ('{value}', 'x')]),
        ),
    ]
