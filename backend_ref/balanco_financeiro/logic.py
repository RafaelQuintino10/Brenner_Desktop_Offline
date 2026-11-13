"""Apuração de caixa por data de recebimento, com comissões históricas."""
import calendar
from datetime import date
from decimal import Decimal
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from .models import Despesa, Fechamento, PeriodoFinanceiro
from barbeiros.models import Barbeiro
from vendas.models import Venda, VendaServico

ZERO = Decimal('0.00')


def normalize_month(value):
    if not isinstance(value, str) or len(value) != 7 or value[4] != '-':
        raise ValidationError({'mes': 'Use o formato YYYY-MM.'})
    try:
        date.fromisoformat(value + '-01')
    except ValueError:
        raise ValidationError({'mes': 'Mês inválido; use YYYY-MM.'})
    return value


def month_range(mes):
    mes = normalize_month(mes)
    year, month = map(int, mes.split('-'))
    beginning = date(year, month, 1)
    ending = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return beginning, ending


def period_is_closed(day):
    if day is None:
        return False
    mes = str(day)[:7]
    return PeriodoFinanceiro.objects.filter(mes=mes, fechado=True).exists() or Fechamento.objects.filter(mes=mes).exists()


def lock_period(day):
    """Chamar apenas dentro de transaction.atomic() para serializar lançamentos e fechamento."""
    mes = normalize_month(str(day)[:7])
    obj, _ = PeriodoFinanceiro.objects.get_or_create(mes=mes)
    obj = PeriodoFinanceiro.objects.select_for_update().get(pk=obj.pk)
    if obj.fechado or Fechamento.objects.filter(mes=mes).exists():
        raise ValidationError({'mes': f'O período {mes} já está fechado.'})
    return obj


def money(value):
    return f'{value:.2f}'


def add(qs, field):
    return qs.aggregate(total=Sum(field))['total'] or ZERO


def summary(mes):
    start, end = month_range(mes)
    servicos = VendaServico.objects.filter(data__gte=start, data__lt=end)
    produtos = Venda.objects.filter(data__gte=start, data__lt=end, estornada=False)
    despesas = Despesa.objects.filter(data__gte=start, data__lt=end)
    ts = add(servicos, 'valor')
    tp = add(produtos, 'valor_total')
    cp = add(produtos, 'custo_total')
    de = add(despesas, 'valor')
    cs = add(servicos, 'comissao')
    cprod = add(produtos, 'comissao')
    repasses = []
    for b in Barbeiro.objects.all():
        s = add(servicos.filter(barbeiro=b), 'comissao')
        p = add(produtos.filter(barbeiro=b), 'comissao')
        if s or p:
            repasses.append({
                'barbeiro_id': b.pk, 'barbeiro': b.nome,
                'servicos': money(s), 'produtos': money(p), 'total': money(s + p),
            })
    fechamento = Fechamento.objects.filter(mes=mes).first()
    return {
        'mes': mes,
        'total_servicos': money(ts),
        'total_produtos': money(tp),
        'receita_bruta': money(ts + tp),
        'custo_produtos': money(cp),
        'despesas': money(de),
        'comissoes_servicos': money(cs),
        'comissoes_produtos': money(cprod),
        'comissoes': money(cs + cprod),
        'saldo_proprietario': money(ts + tp - cp - de - cs - cprod),
        'repasses': repasses,
        'fechado': bool(fechamento),
        'fechado_em': fechamento.fechado_em if fechamento else None,
    }
