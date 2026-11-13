from datetime import date
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Despesa, Fechamento, PeriodoFinanceiro
from .serializers import DespesaSerializer
from .logic import lock_period, normalize_month, period_is_closed, summary
from config.permissions import IsAdminOrBalconista


class DespesaViewSet(viewsets.ModelViewSet):
    queryset = Despesa.objects.all()
    serializer_class = DespesaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        mes = self.request.query_params.get('mes')
        if mes:
            from .logic import month_range
            start, end = month_range(mes)
            qs = qs.filter(data__gte=start, data__lt=end)
        return qs

    def perform_destroy(self, instance):
        with transaction.atomic():
            lock_period(instance.data)
            instance.delete()


class ResumoFinanceiro(APIView):
    def get(self, request):
        mes = normalize_month(request.query_params.get('mes', timezone.localdate().strftime('%Y-%m')))
        return Response(summary(mes))


class FechamentosView(APIView):
    def get(self, request):
        return Response([{
            'mes': f.mes, 'fechado_em': f.fechado_em,
            'saldo_proprietario': str(f.saldo_proprietario), 'repasses': f.repasses,
        } for f in Fechamento.objects.all().order_by('-mes')])

    @transaction.atomic
    def post(self, request):
        mes = normalize_month(request.data.get('mes'))
        # Somente meses já encerrados. Evita bloquear acidentalmente a operação corrente.
        if mes >= timezone.localdate().strftime('%Y-%m'):
            raise ValidationError({'mes': 'Só é possível fechar meses anteriores ao atual.'})
        periodo = lock_period(mes)
        r = summary(mes)
        f = Fechamento.objects.create(
            mes=mes,
            total_servicos=Decimal(r['total_servicos']),
            total_produtos=Decimal(r['total_produtos']),
            custo_produtos=Decimal(r['custo_produtos']),
            despesas=Decimal(r['despesas']),
            comissoes=Decimal(r['comissoes']),
            saldo_proprietario=Decimal(r['saldo_proprietario']),
            repasses=r['repasses'],
        )
        periodo.fechado = True
        periodo.save(update_fields=['fechado'])
        r['fechado'] = True
        r['fechado_em'] = f.fechado_em
        return Response(r, status=status.HTTP_201_CREATED)

class StatusPeriodoFinanceiro(APIView):
    """Informa apenas se o período está fechado."""

    permission_classes = [IsAdminOrBalconista]

    def get(self, request):
        mes = normalize_month(
            request.query_params.get(
                'mes',
                timezone.localdate().strftime('%Y-%m')
            )
        )

        return Response({
            'mes': mes,
            'fechado': period_is_closed(mes),
        })