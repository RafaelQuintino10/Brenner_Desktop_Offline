from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Venda, VendaServico
from barbeiros.models import Barbeiro
from produtos.models import Produto
from balanco_financeiro.logic import lock_period, period_is_closed


# class VendaSerializer(serializers.ModelSerializer):
#     produto_nome = serializers.CharField(source='produto.nome', read_only=True)
#     barbeiro_nome = serializers.CharField(source='barbeiro.nome', read_only=True)
#     data = serializers.DateField(default=timezone.localdate)

#     class Meta:
#         model = Venda
#         fields = [
#             'id', 'produto', 'produto_nome', 'barbeiro', 'barbeiro_nome',
#             'data', 'quantidade', 'preco_unitario', 'custo_unitario',
#             'percentual_comissao', 'valor_total', 'custo_total', 'comissao',
#             'estornada', 'estornada_em', 'criado_em',
#         ]
#         read_only_fields = [
#             'id', 'preco_unitario', 'custo_unitario', 'percentual_comissao',
#             'valor_total', 'custo_total', 'comissao', 'estornada', 'estornada_em', 'criado_em',
#         ]

#     def validate(self, attrs):
#         if self.instance:
#             raise ValidationError('Vendas são imutáveis. Use POST /api/vendas/{id}/estornar/.')
#         if attrs.get('quantidade', 0) < 1:
#             raise ValidationError({'quantidade': 'Informe uma quantidade maior que zero.'})
#         if attrs.get('data', timezone.localdate()) > timezone.localdate():
#             raise ValidationError({'data': 'Não registre recebimento em data futura.'})
#         if not attrs['barbeiro'].ativo:
#             raise ValidationError('O barbeiro precisa estar ativo.')
#         if not attrs['produto'].ativo:
#             raise ValidationError('O produto precisa estar ativo.')
#         if period_is_closed(attrs['data']):
#             raise ValidationError('O mês da venda já foi fechado.')
#         return attrs

#     @transaction.atomic
#     def create(self, validated_data):
#         lock_period(validated_data['data'])
#         produto = Produto.objects.select_for_update().get(pk=validated_data['produto'].pk)
#         barbeiro = Barbeiro.objects.get(pk=validated_data['barbeiro'].pk)
#         qty = validated_data['quantidade']
#         if not produto.ativo or not barbeiro.ativo:
#             raise ValidationError('Produto ou barbeiro desativado.')
#         if produto.estoque < qty:
#             raise ValidationError({'quantidade': f'Estoque insuficiente: {produto.estoque} disponível(is).'})
#         preco = produto.preco
#         custo = produto.custo
#         comissao_pct = barbeiro.comissao_produto
#         total = preco * qty
#         custo_total = custo * qty
#         comissao = (total * comissao_pct / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
#         produto.estoque -= qty
#         produto.save(update_fields=['estoque'])
#         return Venda.objects.create(
#             **validated_data, preco_unitario=preco, custo_unitario=custo,
#             percentual_comissao=comissao_pct, valor_total=total,
#             custo_total=custo_total, comissao=comissao,
#         )


# class VendaBalconistaSerializer(VendaSerializer):
#     """Expõe apenas os campos operacionais da venda."""

#     class Meta(VendaSerializer.Meta):
#         fields = [
#             'id',
#             'produto',
#             'produto_nome',
#             'barbeiro',
#             'barbeiro_nome',
#             'data',
#             'quantidade',
#             'valor_total',
#             'estornada',
#         ]

#         read_only_fields = [
#             'id',
#             'produto_nome',
#             'barbeiro_nome',
#             'valor_total',
#             'estornada',
#         ]



ZERO = Decimal('0.00')


class VendaSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(
        source='produto.nome',
        read_only=True
    )

    barbeiro_nome = serializers.SerializerMethodField()
    data = serializers.DateField(default=timezone.localdate)

    def get_barbeiro_nome(self, obj):
        return (
            obj.barbeiro.nome
            if obj.barbeiro_id
            else 'Administração'
        )

    class Meta:
        model = Venda
        fields = [
            'id', 'produto', 'produto_nome',
            'barbeiro', 'barbeiro_nome',
            'data', 'quantidade',
            'preco_unitario', 'custo_unitario',
            'percentual_comissao',
            'valor_total', 'custo_total', 'comissao',
            'estornada', 'estornada_em', 'criado_em',
        ]

        read_only_fields = [
            'id', 'preco_unitario', 'custo_unitario',
            'percentual_comissao', 'valor_total',
            'custo_total', 'comissao', 'estornada',
            'estornada_em', 'criado_em',
        ]

    def validate(self, attrs):
        instance = self.instance
        user = self.context['request'].user

        if instance and not user.is_staff:
            raise ValidationError(
                'Somente o administrador pode editar vendas.'
            )

        if instance and instance.estornada:
            raise ValidationError(
                'Uma venda estornada não pode ser editada.'
            )

        produto = attrs.get(
            'produto',
            instance.produto if instance else None
        )

        barbeiro = attrs.get(
            'barbeiro',
            instance.barbeiro if instance else None
        )

        quantidade = attrs.get(
            'quantidade',
            instance.quantidade if instance else 0
        )

        data = attrs.get(
            'data',
            instance.data if instance else timezone.localdate()
        )

        # if not instance:
        #     if user.is_staff and barbeiro is None:
        #         raise ValidationError({
        #             'barbeiro': 'Escolha o barbeiro vendedor.'
        #         })

        #     if not user.is_staff:
        #         # Venda do balcão pertence à Administração.
        #         attrs['barbeiro'] = None
        #         barbeiro = None

        # elif instance.barbeiro_id is None and barbeiro is not None:
        #     raise ValidationError({
        #         'barbeiro': (
        #             'Vendas do balcão permanecem '
        #             'atribuídas à administração.'
        #         )
        #     })

        # elif instance.barbeiro_id is not None and barbeiro is None:
        #     raise ValidationError({
        #         'barbeiro': 'Selecione um barbeiro para esta venda.'
        #     })
        if not instance:
            # Mantém a exigência de barbeiro no painel Admin.
            if user.is_staff and barbeiro is None:
                raise ValidationError({
                    'barbeiro': 'Escolha o barbeiro vendedor.'
                })

            # No balcão, respeita a seleção enviada:
            # None = Barbearia / Administração
            # ID = barbeiro selecionado

        elif instance.barbeiro_id is None and barbeiro is not None:
            raise ValidationError({
                'barbeiro': (
                    'Vendas da administração permanecem '
                    'atribuídas à administração.'
                )
            })

        elif instance.barbeiro_id is not None and barbeiro is None:
            raise ValidationError({
                'barbeiro': 'Selecione um barbeiro para esta venda.'
            })

        if quantidade < 1:
            raise ValidationError({
                'quantidade': 'Informe uma quantidade maior que zero.'
            })

        if data > timezone.localdate():
            raise ValidationError({
                'data': 'Não registre vendas em data futura.'
            })

        if produto is None:
            raise ValidationError({
                'produto': 'Selecione o produto.'
            })

        if (
            (not instance or produto.pk != instance.produto_id)
            and not produto.ativo
        ):
            raise ValidationError(
                'O produto precisa estar ativo.'
            )

        if (
            barbeiro
            and (not instance or barbeiro.pk != instance.barbeiro_id)
            and not barbeiro.ativo
        ):
            raise ValidationError(
                'O barbeiro precisa estar ativo.'
            )

        if instance and period_is_closed(instance.data):
            raise ValidationError(
                'O mês original da venda já foi fechado.'
            )

        if period_is_closed(data):
            raise ValidationError(
                'O mês da venda já foi fechado.'
            )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lock_period(validated_data['data'])

        produto = Produto.objects.select_for_update().get(
            pk=validated_data['produto'].pk
        )

        barbeiro = validated_data.get('barbeiro')
        quantidade = validated_data['quantidade']

        if not produto.ativo or (
            barbeiro and not barbeiro.ativo
        ):
            raise ValidationError(
                'Produto ou barbeiro desativado.'
            )

        if produto.estoque < quantidade:
            raise ValidationError({
                'quantidade': (
                    f'Estoque insuficiente: '
                    f'{produto.estoque} disponível(is).'
                )
            })

        preco = produto.preco
        custo = produto.custo

        percentual = (
            barbeiro.comissao_produto
            if barbeiro
            else ZERO
        )

        total = preco * quantidade
        custo_total = custo * quantidade

        comissao = (
            total * percentual / Decimal('100')
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        produto.estoque -= quantidade
        produto.save(update_fields=['estoque'])

        return Venda.objects.create(
            **validated_data,
            preco_unitario=preco,
            custo_unitario=custo,
            percentual_comissao=percentual,
            valor_total=total,
            custo_total=custo_total,
            comissao=comissao,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        venda = Venda.objects.select_for_update().get(
            pk=instance.pk
        )

        if venda.estornada:
            raise ValidationError(
                'Uma venda estornada não pode ser editada.'
            )

        nova_data = validated_data.get(
            'data', venda.data
        )

        # Impede alterações em meses fechados.
        # Bloqueia os períodos em ordem estável.
        meses = sorted({
            str(venda.data)[:7],
            str(nova_data)[:7]
        })

        for mes in meses:
            lock_period(mes)

        novo_produto_id = validated_data.get(
            'produto', venda.produto
        ).pk

        # Bloqueia os produtos envolvidos.
        produtos = {
            p.pk: p
            for p in Produto.objects.select_for_update()
            .filter(
                pk__in={
                    venda.produto_id,
                    novo_produto_id
                }
            )
            .order_by('pk')
        }

        anterior = produtos[venda.produto_id]
        produto = produtos[novo_produto_id]

        quantidade = validated_data.get(
            'quantidade', venda.quantidade
        )

        barbeiro = validated_data.get(
            'barbeiro', venda.barbeiro
        )

        if venda.barbeiro_id is None and barbeiro is not None:
            raise ValidationError(
                'Vendas do balcão pertencem à administração.'
            )

        if venda.barbeiro_id is not None and barbeiro is None:
            raise ValidationError(
                'Barbeiro não pode ser removido desta venda.'
            )

        if (
            not produto.ativo
            and novo_produto_id != venda.produto_id
        ):
            raise ValidationError(
                'O produto selecionado está inativo.'
            )

        if (
            barbeiro
            and barbeiro.pk != venda.barbeiro_id
            and not barbeiro.ativo
        ):
            raise ValidationError(
                'O barbeiro selecionado está inativo.'
            )

        if quantidade < 1 or nova_data > timezone.localdate():
            raise ValidationError(
                'Quantidade ou data inválida.'
            )

        # Devolve a quantidade antiga ao estoque.
        anterior.estoque += venda.quantidade

        # Aplica a nova quantidade ao produto escolhido.
        if produto.estoque < quantidade:
            raise ValidationError({
                'quantidade': (
                    f'Estoque insuficiente: '
                    f'{produto.estoque} disponível(is).'
                )
            })

        produto.estoque -= quantidade

        for p in produtos.values():
            p.save(update_fields=['estoque'])

        # Preserva o preço e o custo históricos
        # quando o produto é mantido.
        preco = (
            venda.preco_unitario
            if venda.produto_id == novo_produto_id
            else produto.preco
        )

        custo = (
            venda.custo_unitario
            if venda.produto_id == novo_produto_id
            else produto.custo
        )

        # Preserva a comissão histórica se o
        # barbeiro não foi alterado.
        percentual = (
            ZERO
            if barbeiro is None
            else (
                venda.percentual_comissao
                if barbeiro.pk == venda.barbeiro_id
                else barbeiro.comissao_produto
            )
        )

        venda.produto = produto
        venda.barbeiro = barbeiro
        venda.data = nova_data
        venda.quantidade = quantidade

        venda.preco_unitario = preco
        venda.custo_unitario = custo
        venda.percentual_comissao = percentual

        venda.valor_total = preco * quantidade
        venda.custo_total = custo * quantidade

        venda.comissao = (
            venda.valor_total * percentual / Decimal('100')
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        venda.save(update_fields=[
            'produto',
            'barbeiro',
            'data',
            'quantidade',
            'preco_unitario',
            'custo_unitario',
            'percentual_comissao',
            'valor_total',
            'custo_total',
            'comissao',
        ])

        return venda


# class VendaBalconistaSerializer(VendaSerializer):
#     class Meta(VendaSerializer.Meta):
#         fields = [
#             'id',
#             'produto',
#             'produto_nome',
#             'barbeiro_nome',
#             'data',
#             'quantidade',
#             'valor_total',
#             'estornada',
#         ]

#         read_only_fields = [
#             'id',
#             'produto_nome',
#             'barbeiro_nome',
#             'valor_total',
#             'estornada',
#         ]
class VendaBalconistaSerializer(VendaSerializer):
    class Meta(VendaSerializer.Meta):
        fields = [
            'id',
            'produto',
            'produto_nome',
            'barbeiro',
            'barbeiro_nome',
            'data',
            'quantidade',
            'valor_total',
            'estornada',
        ]

        read_only_fields = [
            'id',
            'produto_nome',
            'barbeiro_nome',
            'valor_total',
            'estornada',
        ]

class RecebimentoServicoSerializer(serializers.ModelSerializer):
    barbeiro_nome = serializers.CharField(source='barbeiro.nome', read_only=True)

    class Meta:
        model = VendaServico
        fields = ['id', 'agendamento', 'barbeiro', 'barbeiro_nome', 'data', 'valor', 'percentual_comissao', 'comissao']
        read_only_fields = fields
