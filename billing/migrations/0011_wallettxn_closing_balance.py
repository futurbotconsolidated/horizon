# Generated by Django 3.2.5 on 2021-09-29 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0010_alter_couponusage_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallettxn',
            name='closing_balance',
            field=models.FloatField(default=0),
        ),
    ]
