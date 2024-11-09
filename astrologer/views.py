from astrologer.models import Astrologer, Language, Expertise, Favorite
from astrologer.serializers import (
    AstrologerSerializer,
    LanguageSerializer,
    ExpertiseSerializer,
    FavoriteSerializer
)

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework_simplejwt import authentication
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView, CreateAPIView

from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

# class ListAstrologers(ListCreateAPIView):
#     serializer_class = AstrologerSerializer
#     filter_class = AstrologerFilter
#     queryset = Astrologer.objects.all()


class MyPageNumberPagination(PageNumberPagination):
    page_size = 10


class AstrologerViewSet(viewsets.ModelViewSet):
    authentication_classes = [authentication.JWTAuthentication]
    # permission_classes = [IsAuthenticated]
    serializer_class = AstrologerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['language', 'expertise']

    def get_queryset(self):
        sort_by = self.request.GET.get("sort_by")
        queryset = Astrologer.objects.all()
        if sort_by is not None:
            if sort_by == "price_asc":
                queryset = Astrologer.objects.order_by("price")
            if sort_by == "price_desc":
                queryset = Astrologer.objects.order_by("-price")
            if sort_by == "rating_asc":
                queryset = Astrologer.objects.order_by("rating")
            if sort_by == "rating_desc":
                queryset = Astrologer.objects.order_by("-rating")
        return queryset

    # def list(self, request):
    #     queryset = Astrologer.objects.all()
    #     serializer = AstrologerSerializer(queryset, many=True)
    #     return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Astrologer.objects.all()
        astrologer = get_object_or_404(queryset, pk=pk)
        serializer = AstrologerSerializer(astrologer)
        return Response(serializer.data)


class ListLanguages(ListAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class ListExpertise(ListAPIView):
    queryset = Expertise.objects.all()
    serializer_class = ExpertiseSerializer


class CreateFavorite(CreateAPIView):
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def create(self, request, **kwargs):
        astro_obj = get_object_or_404(Astrologer, pk=self.kwargs['pk'])
        favorite = {'astrologer': astro_obj.id, 'customer': request.user.id}
        if Favorite.objects.filter(
            astrologer=astro_obj.id, customer=request.user.id
        ):
            return Response({"message": "Favorite astrologer already exists"})
        serializer = FavoriteSerializer(data=favorite)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
