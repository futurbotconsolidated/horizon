from django.db import models
from aouth.models import CustomUser


class Customer(models.Model):
    MARITAL_STATUS_CHOICES = (
        ('M', 'Married'),
        ('S', 'Single'),
        ('D', 'Divorced')
    )
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_of_birth = models.DateTimeField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=254, null=True, blank=True)
    marital_status = models.CharField(
        max_length=1, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    extra = models.JSONField(default=dict(),null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_complete(self):
        if not (self.user.full_name and self.date_of_birth and
         self.place_of_birth and self.user.gender and
         self.marital_status and self.occupation and
         self.user.phone
         ):
         return False
        else:
            return True

    def __str__(self):
        return self.user.phone


class UserSiteReview(models.Model):
    customer = models.OneToOneField(Customer, on_delete = models.CASCADE)
    rating = models.FloatField()
    review = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    visible = models.BooleanField(default=False)

    def __str__(self):
        return self.review


class UserBookingReview(models.Model):
    customer = models.ForeignKey(Customer, on_delete = models.CASCADE)
    booking = models.OneToOneField(to = 'billing.AstrologyBooking', on_delete = models.CASCADE)
    rating = models.FloatField()
    review = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    visible = models.BooleanField(default=False)

    def __str__(self):
        return self.review