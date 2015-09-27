# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dmd', '0002_auto_20150925_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicator',
            name='number_format',
            field=models.CharField(max_length=32, choices=[('{:.0f}', 'Entier'), ('{:.2f}', 'R\xe9el deux d\xe9cimales'), ('{:.1f}', 'R\xe9el une d\xe9cimale')]),
        ),
        migrations.AlterField(
            model_name='partner',
            name='organization',
            field=models.ForeignKey(default='pnlp', to='dmd.Organization'),
            preserve_default=False,
        ),
    ]
