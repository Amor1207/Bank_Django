# Generated by Django 2.2.10 on 2024-05-04 07:04

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0040_auto_20240504_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrowrecord',
            name='end_day',
            field=models.DateTimeField(default=datetime.datetime(2024, 5, 11, 7, 4, 40, 806898, tzinfo=utc)),
        ),
    ]
