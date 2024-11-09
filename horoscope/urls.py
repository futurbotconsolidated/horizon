from django.urls import path
from django.urls.conf import include
from .views import HoroscopeViewSet
from rest_framework import routers


router = routers.SimpleRouter()
router.register('', HoroscopeViewSet, basename='Horoscope')

urlpatterns = [
    path('', include(router.urls))
]