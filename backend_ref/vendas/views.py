from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from balanco_financeiro.logic import lock_period, month_range
from produtos.models import Produto
from .models import Venda, VendaServico
# from .serializers import VendaSerializer, RecebimentoServicoSerializer
from .serializers import (
    VendaSerializer,
    VendaBalconistaSerializer,
    RecebimentoServicoSerializer,
)

from config.permissions import IsAdminOrBalconista
from rest_framework.permissions import IsAdminUser


# class VendaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
#     queryset = Venda.objects.select_related('produto', 'barbeiro').all()
#     serializer_class = VendaSerializer
# class VendaViewSet(
#     mixins.ListModelMixin,
#     mixins.RetrieveModelMixin,
#     mixins.CreateModelMixin,
#     viewsets.GenericViewSet
# ):
#     permission_classes = [IsAdminOrBalconista]

#     queryset = Venda.objects.select_related(
#         'produto', 'barbeiro'
#     ).all()

#     serializer_class = VendaSerializer
class VendaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAdminOrBalconista]

    queryset = Venda.objects.select_related(
        'produto', 'barbeiro'
    ).all()

    serializer_class = VendaSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsAdminUser()]

        return super().get_permissions()

    # Mantenha os métodos existentes abaixo.

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return VendaSerializer

        return VendaBalconistaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('mes'):
            start, end = month_range(self.request.query_params['mes'])
            qs = qs.filter(data__gte=start, data__lt=end)
        if self.request.query_params.get('barbeiro'):
            qs = qs.filter(barbeiro_id=self.request.query_params['barbeiro'])
        return qs

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def estornar(self, request, pk=None):
        venda = get_object_or_404(Venda.objects.select_for_update(), pk=pk)
        if venda.estornada:
            raise ValidationError('Esta venda já foi estornada.')
        lock_period(venda.data)
        produto = Produto.objects.select_for_update().get(pk=venda.produto_id)
        produto.estoque += venda.quantidade
        produto.save(update_fields=['estoque'])
        venda.estornada = True
        venda.estornada_em = timezone.now()
        venda.save(update_fields=['estornada', 'estornada_em'])
        return Response(self.get_serializer(venda).data, status=status.HTTP_200_OK)


class RecebimentoServicoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = VendaServico.objects.select_related('agendamento', 'barbeiro').all().order_by('-data', '-id')
    serializer_class = RecebimentoServicoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('mes'):
            start, end = month_range(self.request.query_params['mes'])
            qs = qs.filter(data__gte=start, data__lt=end)
        return qs
