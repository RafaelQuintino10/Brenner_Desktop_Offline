from django.db.models.deletion import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from .models import Barbeiro, Folga
# from .serializers import BarbeiroSerializer, FolgaSerializer
from .serializers import (
    BarbeiroSerializer,
    BarbeiroBalconistaSerializer,
    FolgaSerializer,
)

from config.permissions import IsAdminOrBalconistaReadOnly
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from config.upload import UploadImagemSerializer


# class BarbeiroViewSet(viewsets.ModelViewSet):
#     queryset = Barbeiro.objects.prefetch_related('horarios').all()
#     serializer_class = BarbeiroSerializer
class BarbeiroViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrBalconistaReadOnly]

    queryset = Barbeiro.objects.prefetch_related(
        'horarios'
    ).all()

    serializer_class = BarbeiroSerializer

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return BarbeiroSerializer

        return BarbeiroBalconistaSerializer

    @action(
        detail=True,
        methods=['post'],
        url_path='imagem',
        parser_classes=[MultiPartParser, FormParser]
    )
    def enviar_imagem(self, request, pk=None):
        barbeiro = self.get_object()

        serializer = UploadImagemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        barbeiro.foto_arquivo = serializer.validated_data['arquivo']
        barbeiro.save(update_fields=['foto_arquivo'])

        return Response(self.get_serializer(barbeiro).data)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('Existem registros vinculados. Desative o barbeiro em vez de excluí-lo.')


class FolgaViewSet(viewsets.ModelViewSet):
    queryset = Folga.objects.select_related('barbeiro').all()
    serializer_class = FolgaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('barbeiro'):
            qs = qs.filter(barbeiro_id=self.request.query_params['barbeiro'])
        return qs
