from rest_framework import status
from rest_framework.generics import ListCreateAPIView, GenericAPIView, ListAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from api.models import Author, Artworks, Genre
from api.serializer import AuthorSerializer, ArtworksSerializer


class Library(ListModelMixin, GenericAPIView):
    """
    Endpoints для библиотеки
    """
    queryset = Author.objects.all().order_by('name')
    serializer_class = AuthorSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        queryset = self.queryset()
        serializer = AuthorSerializer(queryset, many=True)
        return Response(serializer.data)


class Search(APIView):
    def get(self, request):
        value = request.GET.get('value')
        authors = Author.objects.filter(name__iexact=value)
        artworks = Artworks.objects.filter(name__iexact=value)
        results = {
            'authors': AuthorSerializer(authors, many=True).data,
            'artworks': ArtworksSerializer(artworks, many=True).data,
        }
        return Response(status=status.HTTP_200_OK, data=results)


class FilterArtworks(ListModelMixin, GenericAPIView):
    queryset = Artworks.objects.all()
    serializer_class = ArtworksSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        return Response(
            data=self.serializer_class(self.queryset.filter(name__startswith=request.GET.get('value')), many=True).data,
            status=200
        )

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class FilterAuthor(ListModelMixin, GenericAPIView):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = ()

    def list(self, request, *args, **kwargs):
        return Response(
            data=self.serializer_class(self.queryset.filter(name__startswith=request.GET.get('value')), many=True).data,
            status=200
        )

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class GenreList(ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = Genre


class FirstLetter(APIView):
    def get(self, request):
        letters = {}
        for el in Author.objects.values_list('name'):
            el = el[0]
            if el[0] not in letters:
                letters[el[0]] = 1
            else:
                letters[el[0]] += 1
        return Response(status=200, data=letters)
