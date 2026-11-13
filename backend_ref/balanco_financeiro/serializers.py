from django.db import transaction
from rest_framework import serializers
from .models import Despesa
from .logic import lock_period, period_is_closed


class DespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Despesa
        fields = ['id', 'descricao', 'data', 'valor', 'criado_em']
        read_only_fields = ['id', 'criado_em']

    def validate(self, attrs):
        target = attrs.get('data', self.instance.data if self.instance else None)
        if target and period_is_closed(target):
            raise serializers.ValidationError('O mês dessa despesa já foi fechado.')
        if self.instance and period_is_closed(self.instance.data):
            raise serializers.ValidationError('A despesa pertence a um mês fechado.')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lock_period(validated_data['data'])
        return Despesa.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        # Sempre a mesma ordem de locks caso haja transferência entre meses.
        instance = Despesa.objects.select_for_update().get(pk=instance.pk)
        months = sorted(set([str(instance.data)[:7], str(validated_data.get('data', instance.data))[:7]]))
        for mes in months:
            lock_period(mes)
        return super().update(instance, validated_data)
