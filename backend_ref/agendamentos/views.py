from datetime import date
from django.db import transaction
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
# from rest_framework.permissions import AllowAny
from rest_framework.permissions import AllowAny

from config.permissions import (
    IsAdminOrBalconista,
    IsAdminOrBalconistaReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from barbeiros.models import Barbeiro
from barbeiros.serializers import PublicBarberSerializer
from produtos.models import Produto
from produtos.serializers import PublicProdutoSerializer
from .models import Cliente, Servico, Agendamento
from .serializers import ClienteSerializer, ServicoSerializer, PublicServicoSerializer, AgendamentoSerializer, PublicBookingSerializer
from .logic import available_slots


# class ClienteViewSet(viewsets.ModelViewSet):
#     queryset = Cliente.objects.all()
#     serializer_class = ClienteSerializer
class ClienteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrBalconistaReadOnly]
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('O cliente tem histórico. Mantenha o registro.')


class ServicoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrBalconistaReadOnly]
    queryset = Servico.objects.all()
    serializer_class = ServicoSerializer

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('O serviço tem histórico. Desative-o em vez de excluir.')


# class AgendamentoViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAdminOrBalconistaReadOnly]
#     queryset = Agendamento.objects.select_related('cliente', 'barbeiro', 'servico').all()
#     serializer_class = AgendamentoSerializer
class AgendamentoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrBalconista]
    queryset = Agendamento.objects.select_related(
        'cliente', 'barbeiro', 'servico'
    ).all()
    serializer_class = AgendamentoSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get('data'):
            qs = qs.filter(data=params['data'])
        if params.get('mes'):
            from balanco_financeiro.logic import month_range
            start, end = month_range(params['mes'])
            qs = qs.filter(data__gte=start, data__lt=end)
        if params.get('barbeiro'):
            qs = qs.filter(barbeiro_id=params['barbeiro'])
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        return qs

    def perform_destroy(self, instance):
        from balanco_financeiro.logic import period_is_closed
        if instance.pago or instance.status == 'concluido' or period_is_closed(instance.data):
            raise ValidationError('Atendimento contabilizado ou período fechado; exclusão bloqueada.')
        with transaction.atomic():
            Barbeiro.objects.select_for_update().get(pk=instance.barbeiro_id)
            instance.delete()


def catalog_payload():
    return {
        'barbeiros': PublicBarberSerializer(Barbeiro.objects.filter(ativo=True).prefetch_related('horarios'), many=True).data,
        'servicos': PublicServicoSerializer(Servico.objects.filter(ativo=True), many=True).data,
        'produtos': PublicProdutoSerializer(Produto.objects.filter(ativo=True, estoque__gt=0), many=True).data,
    }


class PublicCatalog(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(catalog_payload())


class PublicBarbers(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(PublicBarberSerializer(Barbeiro.objects.filter(ativo=True).prefetch_related('horarios'), many=True).data)


class PublicServices(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(PublicServicoSerializer(Servico.objects.filter(ativo=True), many=True).data)


class PublicProducts(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(PublicProdutoSerializer(Produto.objects.filter(ativo=True, estoque__gt=0), many=True).data)


class PublicAvailableSlots(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        try:
            barber = Barbeiro.objects.get(pk=request.query_params['barbeiro'], ativo=True)
            service = Servico.objects.get(pk=request.query_params['servico'], ativo=True)
            day = date.fromisoformat(request.query_params['data'])
        except (KeyError, ValueError, Barbeiro.DoesNotExist, Servico.DoesNotExist):
            raise ValidationError('Informe barbeiro, serviço e data válidos.')
        return Response({'data': str(day), 'barbeiro': barber.pk, 'servico': service.pk, 'horarios': available_slots(barber, service, day)})


class PublicBooking(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PublicBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        return Response({
            'id': booking.pk,
            'status': booking.status,
            'mensagem': 'Agendamento recebido. Aguarde a confirmação da barbearia.',
        }, status=status.HTTP_201_CREATED)
