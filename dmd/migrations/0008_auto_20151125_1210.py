# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0007_auto_20151103_0942'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarecord',
            name='validation_status',
            field=models.CharField(default='not_validated', max_length=128, choices=[('validated', 'Validated'), ('auto_validated', 'Auto Validated'), ('not_validated', 'Not Validated'), ('rejected', 'Rejected'), ('modified', 'Modified')]),
        ),
        migrations.AlterField(
            model_name='entity',
            name='etype',
            field=models.CharField(max_length=64, choices=[('pays', 'Country'), ('division_provinciale_sante', 'Division Provinciale de la Sant\xe9'), ('zone_sante', 'Zone de sant\xe9')]),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='collection_level',
            field=models.CharField(max_length=64, choices=[('pays', 'Country'), ('division_provinciale_sante', 'Division Provinciale de la Sant\xe9'), ('zone_sante', 'Zone de sant\xe9')]),
        ),
    ]
