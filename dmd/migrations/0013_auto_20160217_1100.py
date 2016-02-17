# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0012_auto_20151209_1228'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organization',
            options={'ordering': ['name']},
        ),
        migrations.AlterField(
            model_name='datarecord',
            name='arrival_status',
            field=models.CharField(default='arrived', max_length=128, choices=[('late', 'Arrived Late'), ('arrived', 'Arrived'), ('on_time', 'Arrived On Time')]),
        ),
    ]
