from django.contrib import admin
from .models import Customer, UserSiteReview, UserBookingReview
# Register your models here.
admin.site.register(Customer)
admin.site.register(UserSiteReview)
admin.site.register(UserBookingReview)
