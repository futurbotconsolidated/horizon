from rest_framework import serializers
from horoscope.models import Horoscope


class HoroscopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horoscope
        fields = '__all__'
