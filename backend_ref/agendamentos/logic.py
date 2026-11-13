from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from barbeiros.models import Folga, HorarioBarbeiro
from .models import Agendamento


SLOT_STEP_MINUTES = 20


def validate_appointment(barbeiro, servico, data, hora, *, exclude=None, check_past=True):
    """Verifica expediente, folga e sobreposição por intervalo, não apenas hora inicial.

    Chamador deve fazer SELECT FOR UPDATE na linha do barbeiro dentro de transaction.atomic.
    """
    if not barbeiro.ativo or not servico.ativo:
        raise ValidationError('Barbeiro ou serviço desativado.')
    start = datetime.combine(data, hora)
    end = start + timedelta(minutes=servico.duracao_minutos)
    now = timezone.localtime(timezone.now()).replace(tzinfo=None)
    if check_past and start <= now:
        raise ValidationError('Escolha um horário futuro.')
    if Folga.objects.filter(barbeiro=barbeiro, data=data).exists():
        raise ValidationError('O barbeiro não atende nesta data.')
    turnos = HorarioBarbeiro.objects.filter(barbeiro=barbeiro, dia_semana=data.weekday())
    if not any(
        start >= datetime.combine(data, turno.inicio) and end <= datetime.combine(data, turno.fim)
        for turno in turnos
    ):
        raise ValidationError('Horário fora do expediente do barbeiro.')
    ocupados = Agendamento.objects.filter(barbeiro=barbeiro, data=data).exclude(status='cancelado')
    if exclude:
        ocupados = ocupados.exclude(pk=exclude)
    for ocupado in ocupados.only('hora', 'duracao_minutos'):
        busy_start = datetime.combine(data, ocupado.hora)
        busy_end = busy_start + timedelta(minutes=ocupado.duracao_minutos)
        if start < busy_end and end > busy_start:
            raise ValidationError('Horário ocupado. Escolha outro.')


def available_slots(barbeiro, servico, data):
    if not barbeiro.ativo or not servico.ativo or Folga.objects.filter(barbeiro=barbeiro, data=data).exists():
        return []
    slots = []
    for turno in HorarioBarbeiro.objects.filter(barbeiro=barbeiro, dia_semana=data.weekday()):
        cursor = datetime.combine(data, turno.inicio)
        last = datetime.combine(data, turno.fim)
        while cursor + timedelta(minutes=servico.duracao_minutos) <= last:
            try:
                validate_appointment(barbeiro, servico, data, cursor.time())
            except ValidationError:
                pass
            else:
                slots.append(cursor.strftime('%H:%M'))
            cursor += timedelta(minutes=SLOT_STEP_MINUTES)
    return sorted(set(slots))
