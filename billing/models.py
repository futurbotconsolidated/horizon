from django.db import models
from astrologer.models import Astrologer
from aouth.models import CustomUser
from users.models import Customer

# Create your models here.
class AstrologyBooking(models.Model):

    associate = models.ForeignKey(Astrologer, on_delete=models.CASCADE)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    duration = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    invoice = models.ForeignKey('WalletInvoice', on_delete=models.CASCADE)
    cancelled = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Booking for {self.user} with {self.associate}" 


class Invoice(models.Model):

    order_id = models.CharField(max_length=36)
    customer_id = models.IntegerField()
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=13)
    txn_amount = models.FloatField()
    description = models.CharField(max_length=1000)
    details = models.JSONField()
    paygw_order = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    coupon = models.ForeignKey('Coupon', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.order_id


class Coupon(models.Model):

    VALUE_TYPE_CHOICES = (
        ('F','Flat Discount'),
        ('P', 'Percentage Discount')
    )
    COUPON_TYPE_CHOICES = (
        ('B', 'For Booking through Wallet'),
        ('W', 'For Wallet Recharges')
    )
    PLAN_CHOICES = (
        (5, '5 minutes'),
        (15, '15 minutes'),
        (30, '30 minutes'),
        (60, '60 minutes')
    )
    code = models.CharField(max_length=20)
    user_specific = models.BooleanField(default=True,help_text="This will allow only a specific user to access the coupon code.")
    user = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE,help_text="Field ignored if user_specific is checked.")
    plan_specific = models.BooleanField(
        default=False, help_text="This will allow coupon to be applied on specific Plan.")
    plan = models.IntegerField(max_length=1, choices=PLAN_CHOICES, null=True, blank=True)
    value = models.IntegerField()
    value_type = models.CharField(max_length=1, choices=VALUE_TYPE_CHOICES)
    max_discount_value = models.IntegerField(default=0)
    validity = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    coupon_type = models.CharField(max_length=1, choices=VALUE_TYPE_CHOICES)

    def __str__(self):
        return self.code


class GSTPercentage(models.Model):
    percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice = models.ForeignKey('WalletInvoice', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.coupon} used by {self.user}"




# Wallet Models
class Wallet(models.Model):
    balance = models.FloatField(default=0)
    user = models.OneToOneField(Customer, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Wallet for {self.user.user.email}"


class WalletPlan(models.Model):
    name = models.CharField(max_length=50)
    inr_amount = models.IntegerField(default=0)
    cashback_percentage = models.FloatField(default=0)
    single_use = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Recharge with INR {self.inr_amount}"


class WalletPlanUsage(models.Model):
    plan = models.ForeignKey(WalletPlan, on_delete=models.CASCADE)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice = models.ForeignKey('WalletInvoice', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plan} used by {self.user}"


class WalletTxn(models.Model):
    # This will record all the TXNs on wallet
    # Both cash deposits through RZP &
    # Booking deductions
    TXN_TYPE_CHOICES = (
        ('D', 'Debit'),
        ('C', 'Credit')
    )
    order_type = models.CharField(
        max_length=1, choices=TXN_TYPE_CHOICES)
    txn_status = models.IntegerField(default=0)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    txn_amount = models.FloatField()
    txn_amount_sans_tax = models.FloatField(default=0)
    closing_balance = models.FloatField(default=0)
    description = models.CharField(max_length=1000)
    invoice = models.ForeignKey('WalletInvoice', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


class WalletInvoice(models.Model):
    order_id = models.CharField(max_length=36)
    customer_id = models.IntegerField()
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=13)
    txn_amount = models.FloatField()
    description = models.CharField(max_length=1000)
    details = models.JSONField()
    paygw_order = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    success = models.BooleanField(default=False)
    coupon = models.ForeignKey('Coupon', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.order_id
