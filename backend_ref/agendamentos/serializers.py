from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from barbeiros.models import Barbeiro
from balanco_financeiro.logic import lock_period, period_is_closed
from vendas.models import VendaServico
from .models import Cliente, Servico, Agendamento
from .logic import validate_appointment


def only_digits(value):
    return ''.join(c for c in value if c.isdigit())


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'telefone', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    def validate_telefone(self, value):
        phone = only_digits(value)
        if not 10 <= len(phone) <= 13:
            raise serializers.ValidationError('Telefone deve conter DDD e entre 10 e 13 dígitos.')
        return phone


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = ['id', 'nome', 'descricao', 'preco', 'duracao_minutos', 'imagem_url', 'ativo']


class PublicServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = ['id', 'nome', 'descricao', 'preco', 'duracao_minutos', 'imagem_url']


def register_service_payment(booking):
    """Snapshot do serviço: liquida o atendimento no dia atual, não na data da reserva."""
    from balanco_financeiro.logic import lock_period
    hoje = timezone.localdate()
    lock_period(hoje)
    comissao_percent = booking.barbeiro.comissao_servico
    comissao = (booking.valor_cobrado * comissao_percent / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    VendaServico.objects.create(
        agendamento=booking,
        barbeiro=booking.barbeiro,
        data=hoje,
        valor=booking.valor_cobrado,
        percentual_comissao=comissao_percent,
        comissao=comissao,
    )


class AgendamentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(write_only=True, required=False)
    cliente_telefone = serializers.CharField(write_only=True, required=False)
    nome_cliente = serializers.CharField(source='cliente.nome', read_only=True)
    telefone_cliente = serializers.CharField(source='cliente.telefone', read_only=True)
    barbeiro_nome = serializers.CharField(source='barbeiro.nome', read_only=True)
    servico_nome = serializers.CharField(source='servico.nome', read_only=True)

    class Meta:
        model = Agendamento
        fields = [
            'id', 'cliente', 'cliente_nome', 'cliente_telefone', 'nome_cliente', 'telefone_cliente',
            'barbeiro', 'barbeiro_nome', 'servico', 'servico_nome', 'data', 'hora',
            'duracao_minutos', 'status', 'pago', 'valor_cobrado', 'observacao', 'criado_em',
        ]
        read_only_fields = ['id', 'duracao_minutos', 'criado_em']
        extra_kwargs = {'cliente': {'required': False}, 'valor_cobrado': {'required': False}}

    def validate(self, attrs):
        instance = self.instance
        barber = attrs.get('barbeiro', instance.barbeiro if instance else None)
        servico = attrs.get('servico', instance.servico if instance else None)
        dia = attrs.get('data', instance.data if instance else None)
        hora = attrs.get('hora', instance.hora if instance else None)
        if not all((barber, servico, dia, hora)):
            raise ValidationError('Informe barbeiro, serviço, data e hora.')
        if instance and instance.pago:
            raise ValidationError('O atendimento já foi pago; não pode ser alterado.')
        status = attrs.get('status', instance.status if instance else 'pendente')
        pago = attrs.get('pago', instance.pago if instance else False)
        if pago and status != 'concluido':
            raise ValidationError('Só é possível pagar um atendimento concluído.')
        if status == 'concluido' and not pago:
            raise ValidationError('Para concluir, informe pago=true.')
        if instance and instance.status == 'cancelado' and status != 'cancelado':
            raise ValidationError('Não reabra reservas canceladas; crie um novo agendamento.')
        if instance and instance.status == 'concluido':
            raise ValidationError('Atendimento concluído não pode ser alterado.')
        if not instance and (status in ('cancelado', 'concluido') or pago):
            raise ValidationError('Crie o agendamento como pendente ou confirmado.')
        if 'valor_cobrado' in attrs and attrs['valor_cobrado'] < 0:
            raise ValidationError({'valor_cobrado': 'Valor não pode ser negativo.'})
        changed_schedule = any(k in attrs for k in ('barbeiro', 'servico', 'data', 'hora'))
        if instance and period_is_closed(instance.data) and changed_schedule:
            raise ValidationError('Agendamento de mês fechado não pode ser remarcado.')
        if (not instance or changed_schedule) and period_is_closed(dia):
            raise ValidationError('Este mês já foi fechado.')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        client_name = validated_data.pop('cliente_nome', '').strip()
        client_phone = only_digits(validated_data.pop('cliente_telefone', ''))
        client = validated_data.get('cliente')
        if not client and (not client_name or not 10 <= len(client_phone) <= 13):
            raise ValidationError('Informe nome e telefone com DDD válidos ou selecione um cliente.')
        barber = Barbeiro.objects.select_for_update().get(pk=validated_data['barbeiro'].pk)
        validate_appointment(barber, validated_data['servico'], validated_data['data'], validated_data['hora'])
        if not client:
            client, _ = Cliente.objects.get_or_create(telefone=client_phone, defaults={'nome': client_name})
            validated_data['cliente'] = client
        validated_data['duracao_minutos'] = validated_data['servico'].duracao_minutos
        validated_data.setdefault('valor_cobrado', validated_data['servico'].preco)
        return Agendamento.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('cliente_nome', None)
        validated_data.pop('cliente_telefone', None)
        target_barber = validated_data.get('barbeiro', instance.barbeiro)
        # Bloquear barbeiro original e novo em ordem fixa para evitar concorrência/deadlocks.
        list(Barbeiro.objects.select_for_update().filter(pk__in=[instance.barbeiro_id, target_barber.pk]).order_by('pk').values_list('pk', flat=True))
        instance = Agendamento.objects.select_for_update().get(pk=instance.pk)
        if instance.pago or instance.status == 'concluido':
            raise ValidationError('Atendimento já contabilizado; alteração bloqueada.')
        changed_schedule = any(k in validated_data for k in ['barbeiro', 'servico', 'data', 'hora'])
        new_status = validated_data.get('status', instance.status)
        if changed_schedule and new_status != 'cancelado':
            validate_appointment(
                target_barber, validated_data.get('servico', instance.servico),
                validated_data.get('data', instance.data), validated_data.get('hora', instance.hora),
                exclude=instance.pk,
            )
        if 'servico' in validated_data:
            validated_data['duracao_minutos'] = validated_data['servico'].duracao_minutos
            if 'valor_cobrado' not in validated_data:
                validated_data['valor_cobrado'] = validated_data['servico'].preco
        if new_status == 'concluido' and validated_data.get('pago', instance.pago):
            # Bloqueio financeiro antes de salvar alteração para garantir rollback se mês fechado.
            lock_period(timezone.localdate())
        instance = super().update(instance, validated_data)
        if instance.status == 'concluido' and instance.pago:
            register_service_payment(instance)
        return instance


class PublicBookingSerializer(AgendamentoSerializer):
    cliente = serializers.PrimaryKeyRelatedField(read_only=True)
    cliente_nome = serializers.CharField(write_only=True, required=True)
    cliente_telefone = serializers.CharField(write_only=True, required=True)

    class Meta(AgendamentoSerializer.Meta):
        read_only_fields = AgendamentoSerializer.Meta.read_only_fields + ['status', 'pago', 'valor_cobrado', 'cliente']

    def create(self, validated_data):
        validated_data['status'] = 'pendente'
        validated_data['pago'] = False
        return super().create(validated_data)
