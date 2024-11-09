from django.urls import path
from .views import LoginOTPView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('login/', LoginOTPView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]