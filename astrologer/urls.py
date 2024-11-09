from django.urls import path
from django.urls.conf import include
from .views import AstrologerViewSet, ListLanguages, ListExpertise, CreateFavorite
from rest_framework import routers


router = routers.SimpleRouter()
router.register('', AstrologerViewSet, basename='Astrologer')

urlpatterns = [
    path('language/', ListLanguages.as_view()),
    path('expertise/', ListExpertise.as_view()),
    path('<int:pk>/favorite/', CreateFavorite.as_view()),
    path('', include(router.urls)),
]