# Generated by Django 2.2.10 on 2024-05-01 02:34

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('book', '0031_auto_20240429_2334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='borrowrecord',
            name='end_day',
            field=models.DateTimeField(default=datetime.datetime(2024, 5, 8, 2, 34, 48, 120267, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='publisher',
            name='updated_by',
            field=models.CharField(default='yaozeliang', max_length=20),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(max_length=50)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(max_length=50)),
                ('transaction_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('completion_date', models.DateTimeField(blank=True, null=True)),
                ('description', models.CharField(max_length=255)),
                ('payment_method', models.CharField(blank=True, max_length=50, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
