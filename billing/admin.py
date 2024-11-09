from django.contrib import admin
from .models import AstrologyBooking, Invoice, Coupon, GSTPercentage, CouponUsage, Wallet, WalletPlan, WalletPlanUsage, WalletTxn, WalletInvoice

admin.site.register(AstrologyBooking)
admin.site.register(Invoice)
admin.site.register(Coupon)
admin.site.register(GSTPercentage)

admin.site.register(CouponUsage)
admin.site.register(Wallet)
admin.site.register(WalletTxn)
admin.site.register(WalletInvoice)
admin.site.register(WalletPlan)
admin.site.register(WalletPlanUsage)

