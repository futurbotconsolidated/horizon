from django.urls import path
from django.urls.conf import include
from .views import (
    UserVerifyCheck,
    UserBookingRetrieve,
    UserProfile,
    UserBookingList,
    UserBooking,
    UserBookingCallback,
    UserSiteFeedback,
    UserBookingFeedback,
    ProfilePictureView
)
from rest_framework import routers

from billing.views import (
    WalletBalCheck,
    WalletAddBal,
    WalletPlans,
    WalletRechargeCallback,
    WalletTXNViewSet
)


router = routers.SimpleRouter()
# router.register('profile', UserProfile, basename='User Profile')
router.register('wallet/history', WalletTXNViewSet, basename='WalletTXNs')
# router.register('bookings', UserBookingList, basename='User Bookings')

urlpatterns = [
    path('check/', UserVerifyCheck.as_view(),
         name='User profile and verify check.'),
    path('', include(router.urls)),
    path('profile/', UserProfile.as_view()),
    path('bookings/<int:pk>/', UserBookingRetrieve.as_view()),
    path('bookings/', UserBookingList.as_view()),
    path('book/', UserBooking.as_view()),
    path('book/callback/<order>/', UserBookingCallback.as_view()),
    # Wallet - billing app
    path('wallet/', WalletBalCheck.as_view()),
    path('wallet/recharge/', WalletAddBal.as_view()),
    path('wallet/plans/', WalletPlans.as_view()),
    path('wallet/callback/<order>/', WalletRechargeCallback.as_view()),
    path('feedback/site/', UserSiteFeedback.as_view()),
    path('feedback/booking/', UserBookingFeedback.as_view()),
    path('profile/picture/', ProfilePictureView.as_view())
]
