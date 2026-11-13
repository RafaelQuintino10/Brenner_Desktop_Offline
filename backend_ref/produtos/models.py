from django.db import models
from django.core.validators import MinValueValidator


class Produto(models.Model):
    nome = models.CharField(max_length=150)
    categoria = models.CharField(max_length=70, default='Outros')
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    custo = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    estoque = models.PositiveIntegerField(default=0)
    estoque_minimo = models.PositiveIntegerField(default=5)
    imagem_url = models.URLField(blank=True)
    imagem_arquivo = models.ImageField(
    upload_to='produtos/',
    blank=True,
    null=True
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome
