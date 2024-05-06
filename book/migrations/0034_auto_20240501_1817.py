# Generated by Django 2.2.10 on 2024-05-01 22:17

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0033_auto_20240501_1611'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='book.Transaction'),
        ),
        migrations.AlterField(
            model_name='borrowrecord',
            name='end_day',
            field=models.DateTimeField(default=datetime.datetime(2024, 5, 8, 22, 17, 55, 299803, tzinfo=utc)),
        ),
    ]
