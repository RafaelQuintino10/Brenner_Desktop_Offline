from django.db import models
from barbeiros.models import Barbeiro
from produtos.models import Produto
from agendamentos.models import Agendamento


class Venda(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT)
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, null=True, blank=True,related_name='vendas_produtos')
    data = models.DateField()
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    percentual_comissao = models.DecimalField(max_digits=5, decimal_places=2)
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    custo_total = models.DecimalField(max_digits=12, decimal_places=2)
    comissao = models.DecimalField(max_digits=12, decimal_places=2)
    estornada = models.BooleanField(default=False)
    estornada_em = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-criado_em']


class VendaServico(models.Model):
    """Recebimento imutável de um atendimento, com comissão congelada."""
    agendamento = models.OneToOneField(Agendamento, on_delete=models.PROTECT, related_name='recebimento')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT)
    data = models.DateField()  # Dia em que foi recebido, não necessariamente dia agendado.
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    percentual_comissao = models.DecimalField(max_digits=5, decimal_places=2)
    comissao = models.DecimalField(max_digits=10, decimal_places=2)
