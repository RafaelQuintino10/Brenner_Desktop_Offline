from django.db import transaction
from rest_framework import serializers
from .models import Barbeiro, Folga, HorarioBarbeiro


class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioBarbeiro
        fields = ['id', 'dia_semana', 'inicio', 'fim']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['fim'] <= attrs['inicio']:
            raise serializers.ValidationError('Horário final precisa ser posterior ao inicial.')
        return attrs


class BarbeiroSerializer(serializers.ModelSerializer):
    horarios = HorarioSerializer(many=True, required=False)
    foto_exibicao = serializers.SerializerMethodField()

    def get_foto_exibicao(self, obj):
        if obj.foto_arquivo:
            request = self.context.get('request')
            url = obj.foto_arquivo.url
            return request.build_absolute_uri(url) if request else url

        return obj.foto_url

    class Meta:
        model = Barbeiro
        fields = [
            'id', 'nome', 'telefone', 'especialidade',
            'comissao_servico', 'comissao_produto', 'ativo', 'foto_url', 'foto_arquivo', 'horarios', 'foto_exibicao'
        ]

    def validate_horarios(self, value):
        dias = {}
        for h in value:
            dias.setdefault(h['dia_semana'], []).append((h['inicio'], h['fim']))
        for turnos in dias.values():
            turnos.sort()
            for anterior, proximo in zip(turnos, turnos[1:]):
                if anterior[1] > proximo[0]:
                    raise serializers.ValidationError('Os turnos de trabalho estão sobrepostos.')
        return value

    @transaction.atomic
    def create(self, validated_data):
        slots = validated_data.pop('horarios', None)
        barber = Barbeiro.objects.create(**validated_data)
        if slots is None:
            slots = [
                {'dia_semana': dia, 'inicio': inicio, 'fim': fim}
                for dia in range(6)
                for inicio, fim in [('08:00', '11:40'), ('14:00', '19:40')]
            ]
        HorarioBarbeiro.objects.bulk_create([HorarioBarbeiro(barbeiro=barber, **h) for h in slots])
        return barber

    @transaction.atomic
    def update(self, instance, validated_data):
        slots = validated_data.pop('horarios', None)
        instance = Barbeiro.objects.select_for_update().get(pk=instance.pk)
        instance = super().update(instance, validated_data)
        if slots is not None:
            instance.horarios.all().delete()
            HorarioBarbeiro.objects.bulk_create([HorarioBarbeiro(barbeiro=instance, **h) for h in slots])
        return instance


class BarbeiroBalconistaSerializer(BarbeiroSerializer):
    class Meta(BarbeiroSerializer.Meta):
        fields = [
            'id',
            'nome',
            'especialidade',
            'ativo',
            'horarios',
            'foto_exibicao',
        ]

class PublicBarberSerializer(serializers.ModelSerializer):
    horarios = HorarioSerializer(many=True, read_only=True)

    class Meta:
        model = Barbeiro
        fields = ['id', 'nome', 'especialidade', 'foto_url', 'horarios']


class FolgaSerializer(serializers.ModelSerializer):
    barbeiro_nome = serializers.CharField(source='barbeiro.nome', read_only=True)

    class Meta:
        model = Folga
        fields = ['id', 'barbeiro', 'barbeiro_nome', 'data', 'motivo']

    def validate(self, attrs):
        from agendamentos.models import Agendamento
        barbeiro = attrs.get('barbeiro', self.instance.barbeiro if self.instance else None)
        dia = attrs.get('data', self.instance.data if self.instance else None)
        if not barbeiro or not dia:
            raise serializers.ValidationError('Informe barbeiro e data.')
        if Agendamento.objects.filter(barbeiro=barbeiro, data=dia).exclude(status='cancelado').exists():
            raise serializers.ValidationError('Existem agendamentos neste dia. Cancele ou remaneje-os primeiro.')
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            Barbeiro.objects.select_for_update().get(pk=validated_data['barbeiro'].pk)
            self.validate(validated_data)
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            barbeiro = validated_data.get('barbeiro', instance.barbeiro)
            list(Barbeiro.objects.select_for_update().filter(pk__in=[instance.barbeiro_id, barbeiro.pk]).order_by('pk').values_list('pk', flat=True))
            self.validate(validated_data)
            return super().update(instance, validated_data)
