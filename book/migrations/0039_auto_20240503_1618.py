# Generated by Django 2.2.10 on 2024-05-03 20:18

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0038_auto_20240502_2228'),
    ]

    operations = [
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('account_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='book.Account')),
                ('loan_amount', models.DecimalField(decimal_places=2, help_text='Total amount of the loan', max_digits=12)),
                ('loan_term', models.IntegerField(help_text='Term of the loan in months')),
                ('monthly_payment', models.DecimalField(blank=True, decimal_places=2, help_text='Monthly repayment amount', max_digits=10, null=True)),
                ('start_date', models.DateField(default=django.utils.timezone.now, help_text='The date when the loan was issued')),
                ('due_date', models.DateField(help_text='The date by which the loan should be fully repaid')),
            ],
            bases=('book.account',),
        ),
        migrations.AlterField(
            model_name='borrowrecord',
            name='end_day',
            field=models.DateTimeField(default=datetime.datetime(2024, 5, 10, 20, 18, 10, 945566, tzinfo=utc)),
        ),
        migrations.CreateModel(
            name='HomeLoan',
            fields=[
                ('loan_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='book.Loan')),
                ('property_address', models.CharField(help_text='Address of the property', max_length=255)),
                ('property_value', models.DecimalField(decimal_places=2, help_text='Appraised value of the property', max_digits=12)),
            ],
            bases=('book.loan',),
        ),
        migrations.CreateModel(
            name='StudentLoan',
            fields=[
                ('loan_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='book.Loan')),
                ('school_name', models.CharField(help_text='Name of the institution', max_length=255)),
                ('course', models.CharField(help_text='Course of study', max_length=255)),
            ],
            bases=('book.loan',),
        ),
    ]