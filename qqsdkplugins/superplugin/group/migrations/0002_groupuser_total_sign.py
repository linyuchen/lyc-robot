# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-08 07:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupuser',
            name='total_sign',
            field=models.IntegerField(default=0),
        ),
    ]
