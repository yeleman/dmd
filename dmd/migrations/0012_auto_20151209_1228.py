# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0011_auto_20151209_1228'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarecord',
            name='arrival_status',
            field=models.CharField(default='arrived', max_length=128, choices=[('late', 'Late'), ('arrived', 'Arrived'), ('on_time', 'On Time')]),
        ),
    ]
