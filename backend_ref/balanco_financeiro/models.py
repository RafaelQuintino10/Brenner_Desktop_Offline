from django.db import models
from django.core.validators import MinValueValidator


class PeriodoFinanceiro(models.Model):
    """Linha de lock por YYYY-MM: impede concorrência entre lançamentos e fechamento."""
    mes = models.CharField(max_length=7, unique=True)
    fechado = models.BooleanField(default=False)

    def __str__(self):
        return self.mes


class Despesa(models.Model):
    descricao = models.CharField(max_length=200)
    data = models.DateField()
    valor = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.descricao}: {self.valor}'


class Fechamento(models.Model):
    mes = models.CharField(max_length=7, unique=True)
    total_servicos = models.DecimalField(max_digits=12, decimal_places=2)
    total_produtos = models.DecimalField(max_digits=12, decimal_places=2)
    custo_produtos = models.DecimalField(max_digits=12, decimal_places=2)
    despesas = models.DecimalField(max_digits=12, decimal_places=2)
    comissoes = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_proprietario = models.DecimalField(max_digits=12, decimal_places=2)
    repasses = models.JSONField(default=list)
    fechado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mes
