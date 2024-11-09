from rest_framework import serializers
from aouth.serializers import CustomUserSerializer
from astrologer.models import Astrologer, Language, Expertise, Favorite


class AstrologerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    language = serializers.StringRelatedField(many=True)
    expertise = serializers.StringRelatedField(many=True)

    class Meta:
        model = Astrologer
        fields = '__all__'


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class ExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = '__all__'


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'
