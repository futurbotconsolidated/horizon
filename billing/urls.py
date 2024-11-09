from django.urls import path
from django.urls.conf import include
from .views import BookingViewSet, UserCouponCheck
from rest_framework import routers


urlpatterns = [
    path('slots/<int:astrologer>/', BookingViewSet.as_view()),
    path('coupon/', UserCouponCheck.as_view()),
]
