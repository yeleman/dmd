# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0006_auto_20151012_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='geometry',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='latitude',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='longitude',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
