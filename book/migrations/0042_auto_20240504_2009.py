# Generated by Django 2.2.10 on 2024-05-05 00:09

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0041_auto_20240504_0304'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='loan',
            options={'ordering': ['-start_date'], 'verbose_name': 'Loan', 'verbose_name_plural': 'Loans'},
        ),
        migrations.AddField(
            model_name='loan',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('overdue', 'Overdue'), ('paid_off', 'Paid Off')], default='active', help_text='Current status of the loan', max_length=10),
        ),
        migrations.AlterField(
            model_name='borrowrecord',
            name='end_day',
            field=models.DateTimeField(default=datetime.datetime(2024, 5, 12, 0, 9, 3, 636570, tzinfo=utc)),
        ),
    ]
