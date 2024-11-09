from horoscope.models import Horoscope
from horoscope.serializers import HoroscopeSerializer

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework_simplejwt import authentication
from rest_framework.response import Response



class HoroscopeViewSet(viewsets.ViewSet):
    authentication_classes = [authentication.JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def list(self, request):
        queryset = Horoscope.objects.all()
        serializer = HoroscopeSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Horoscope.objects.all()
        astrologer = get_object_or_404(queryset, pk=pk)
        serializer = HoroscopeSerializer(astrologer)
        return Response(serializer.data)