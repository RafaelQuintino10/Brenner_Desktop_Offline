from urllib.parse import quote
from django.conf import settings
from rest_framework import serializers
from django.db import transaction
from .models import Produto


class ProdutoSerializer(serializers.ModelSerializer):
    estoque_baixo = serializers.SerializerMethodField()
    imagem_exibicao = serializers.SerializerMethodField()

    def get_imagem_exibicao(self, obj):
        if obj.imagem_arquivo:
            request = self.context.get('request')
            url = obj.imagem_arquivo.url
            return request.build_absolute_uri(url) if request else url

        return obj.imagem_url

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'categoria', 'descricao', 'preco', 'custo', 'estoque', 'estoque_minimo', 'imagem_url', 'imagem_arquivo', 'ativo', 'estoque_baixo', 'imagem_exibicao']

    def get_estoque_baixo(self, obj):
        return obj.estoque <= obj.estoque_minimo

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Produto.objects.select_for_update().get(pk=instance.pk)
        return super().update(instance, validated_data)


class ProdutoBalconistaSerializer(ProdutoSerializer):
    class Meta(ProdutoSerializer.Meta):
        fields = [
            'id',
            'nome',
            'categoria',
            'descricao',
            'preco',
            'estoque',
            'estoque_minimo',
            'ativo',
            'imagem_exibicao',
        ]



class PublicProdutoSerializer(serializers.ModelSerializer):
    whatsapp_url = serializers.SerializerMethodField()
    imagem_exibicao = serializers.SerializerMethodField()

    def get_imagem_exibicao(self, obj):
        if obj.imagem_arquivo:
            request = self.context.get('request')
            url = obj.imagem_arquivo.url
            return request.build_absolute_uri(url) if request else url

        return obj.imagem_url

    class Meta:
        model = Produto
        fields = ['id', 'nome', 'categoria', 'descricao', 'preco', 'imagem_url', 'imagem_arquivo', 'imagem_exibicao', 'whatsapp_url']

    def get_whatsapp_url(self, obj):
        mensagem = f'Olá! Tenho interesse em comprar {obj.nome}, anunciado por R$ {obj.preco:.2f}. Está disponível?'
        return f'https://wa.me/{settings.BARBEARIA_WHATSAPP}?text={quote(mensagem)}'
