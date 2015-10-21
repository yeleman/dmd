# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0005_auto_20151008_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='can_validate',
            field=models.BooleanField(default=False, verbose_name='Can Validate?'),
        ),
    ]
