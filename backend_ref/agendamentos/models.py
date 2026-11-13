from django.db import models
from django.core.validators import MinValueValidator
from barbeiros.models import Barbeiro


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=25, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Servico(models.Model):
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    duracao_minutos = models.PositiveSmallIntegerField(default=40, validators=[MinValueValidator(10)])
    imagem_url = models.URLField(blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Agendamento(models.Model):
    STATUS = [
        ('pendente', 'Pendente'), ('confirmado', 'Confirmado'),
        ('concluido', 'Concluído'), ('cancelado', 'Cancelado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='agendamentos')
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.PROTECT, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, related_name='agendamentos')
    data = models.DateField()
    hora = models.TimeField()
    duracao_minutos = models.PositiveSmallIntegerField(default=40)  # snapshot para evitar mudar agendamento antigo
    status = models.CharField(max_length=12, choices=STATUS, default='pendente')
    pago = models.BooleanField(default=False)
    valor_cobrado = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    observacao = models.CharField(max_length=250, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-hora']
        indexes = [models.Index(fields=['barbeiro', 'data', 'hora'], name='booking_barber_date_time_idx')]

    def __str__(self):
        return f'{self.cliente.nome} - {self.data} {self.hora}'
