from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .models import Produto
# from .serializers import ProdutoSerializer
from .serializers import (
    ProdutoSerializer,
    ProdutoBalconistaSerializer,
)

from config.permissions import IsAdminOrBalconistaReadOnly
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from config.upload import UploadImagemSerializer


# class ProdutoViewSet(viewsets.ModelViewSet):
#     queryset = Produto.objects.all()
#     serializer_class = ProdutoSerializer

class ProdutoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrBalconistaReadOnly]

    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ProdutoSerializer

        return ProdutoBalconistaSerializer

    @action(
    detail=True,
    methods=['post'],
    url_path='imagem',
    parser_classes=[MultiPartParser, FormParser]
    )
    def enviar_imagem(self, request, pk=None):
        produto = self.get_object()

        serializer = UploadImagemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        produto.imagem_arquivo = serializer.validated_data['arquivo']
        produto.save(update_fields=['imagem_arquivo'])

        return Response(self.get_serializer(produto).data)
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('categoria'):
            qs = qs.filter(categoria__iexact=self.request.query_params['categoria'])
        return qs

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('Existem vendas deste produto. Desative em vez de excluir.')
