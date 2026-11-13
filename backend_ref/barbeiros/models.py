from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Barbeiro(models.Model):
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=22, blank=True)
    especialidade = models.CharField(max_length=120, default='Corte masculino')
    comissao_servico = models.DecimalField(max_digits=5, decimal_places=2, default=40, validators=[MinValueValidator(0), MaxValueValidator(100)])
    comissao_produto = models.DecimalField(max_digits=5, decimal_places=2, default=10, validators=[MinValueValidator(0), MaxValueValidator(100)])
    ativo = models.BooleanField(default=True)
    foto_url = models.URLField(blank=True)
    foto_arquivo = models.ImageField(
    upload_to='barbeiros/',
    blank=True,
    null=True
    )

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class HorarioBarbeiro(models.Model):
    DIAS = [(i, n) for i, n in enumerate(['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'])]
    barbeiro = models.ForeignKey(Barbeiro, related_name='horarios', on_delete=models.CASCADE)
    dia_semana = models.PositiveSmallIntegerField(choices=DIAS)
    inicio = models.TimeField()
    fim = models.TimeField()

    class Meta:
        ordering = ['dia_semana', 'inicio']
        unique_together = [('barbeiro', 'dia_semana', 'inicio')]

    def clean(self):
        if self.inicio and self.fim and self.fim <= self.inicio:
            raise ValidationError('Fim precisa ser posterior ao início.')


class Folga(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, related_name='folgas', on_delete=models.CASCADE)
    data = models.DateField()
    motivo = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ['data']
        constraints = [models.UniqueConstraint(fields=['barbeiro', 'data'], name='unique_barber_day_off')]

    def __str__(self):
        return f'{self.barbeiro.nome}: {self.data}'
