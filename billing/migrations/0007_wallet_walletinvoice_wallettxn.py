# Generated by Django 3.2.5 on 2021-09-14 18:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('billing', '0006_alter_coupon_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='users.customer')),
            ],
        ),
        migrations.CreateModel(
            name='WalletInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=36)),
                ('customer_id', models.IntegerField()),
                ('customer_email', models.EmailField(max_length=254)),
                ('customer_phone', models.CharField(max_length=13)),
                ('txn_amount', models.FloatField()),
                ('description', models.CharField(max_length=1000)),
                ('details', models.JSONField()),
                ('paygw_order', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('success', models.BooleanField(default=False)),
                ('coupon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='billing.coupon')),
            ],
        ),
        migrations.CreateModel(
            name='WalletTxn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_type', models.CharField(choices=[('D', 'Debit'), ('C', 'Credit')], max_length=1)),
                ('txn_amount', models.FloatField()),
                ('description', models.CharField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billing.walletinvoice')),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='billing.wallet')),
            ],
        ),
    ]
