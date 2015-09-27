# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0003_auto_20150927_1502'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metadata',
            fields=[
                ('key', models.CharField(max_length=128, serialize=False, primary_key=True)),
                ('value', models.CharField(max_length=512)),
                ('updated_on', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
