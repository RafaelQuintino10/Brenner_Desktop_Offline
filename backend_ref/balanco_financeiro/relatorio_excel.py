
"""Exportação detalhada por mês, baseada em lançamentos reais no PostgreSQL.

Receita de serviços usa VendaServico.data (dia do recebimento);
receita de produto usa Venda.data, ignorando vendas estornadas.
Agendamentos são listados pelo dia da agenda e não contam como receita.
"""
from collections import defaultdict
from decimal import Decimal

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.views import APIView

from agendamentos.models import Agendamento
from barbeiros.models import Barbeiro
from vendas.models import Venda, VendaServico
from .logic import month_range, normalize_month, summary
from .models import Despesa
from .xlsx_writer import Money, Percent, Formula, workbook_bytes

ZERO = Decimal('0.00')


def d(value):
    return Decimal(str(value or 0))


def m(value):
    return Money(d(value))


def build_report(mes):
    """Gera um Excel válido com valores de caixa e comissões históricas."""
    start, end = month_range(mes)
    received = list(
        VendaServico.objects.filter(data__gte=start, data__lt=end)
        .select_related('agendamento__cliente', 'agendamento__servico', 'barbeiro')
        .order_by('data', 'id')
    )
    bookings = list(
        Agendamento.objects.filter(data__gte=start, data__lt=end)
        .select_related('cliente', 'servico', 'barbeiro')
        .order_by('data', 'hora', 'id')
    )
    products = list(
        Venda.objects.filter(data__gte=start, data__lt=end, estornada=False)
        .select_related('produto', 'barbeiro')
        .order_by('data', 'id')
    )
    expenses = list(Despesa.objects.filter(data__gte=start, data__lt=end).order_by('data', 'id'))
    barbers = list(Barbeiro.objects.order_by('nome', 'id'))
    balances = summary(mes)

    service_rows = [[
        'Recebido em', 'Data agendada', 'Hora', 'Cliente', 'Telefone',
        'Serviço', 'Barbeiro', 'Receita (R$)', 'Comissão (%)', 'Comissão (R$)', 'Após comissão (R$)',
    ]]
    commissions = defaultdict(lambda: {
        'services': 0, 'service_revenue': ZERO, 'service_commission': ZERO,
        'units': 0, 'product_revenue': ZERO, 'product_commission': ZERO,
    })
    unique_served_clients = set()
    for receipt in received:
        booking = receipt.agendamento
        unique_served_clients.add(booking.cliente_id)
        entry = commissions[receipt.barbeiro_id]
        entry['services'] += 1
        entry['service_revenue'] += receipt.valor
        entry['service_commission'] += receipt.comissao
        excel_row = len(service_rows) + 1
        service_rows.append([
            receipt.data.isoformat(), booking.data.isoformat(), booking.hora.strftime('%H:%M'),
            booking.cliente.nome, booking.cliente.telefone,
            booking.servico.nome, receipt.barbeiro.nome,
            m(receipt.valor), Percent(receipt.percentual_comissao), m(receipt.comissao),
            Formula(f'H{excel_row}-J{excel_row}', receipt.valor - receipt.comissao),
        ])

    booking_rows = [[
        'Data', 'Hora', 'Cliente', 'Telefone', 'Serviço', 'Barbeiro',
        'Status', 'Pago?', 'Valor previsto (R$)',
    ]]
    for booking in bookings:
        booking_rows.append([
            booking.data.isoformat(), booking.hora.strftime('%H:%M'),
            booking.cliente.nome, booking.cliente.telefone,
            booking.servico.nome, booking.barbeiro.nome,
            booking.get_status_display(), 'Sim' if booking.pago else 'Não',
            m(booking.valor_cobrado),
        ])

    sale_rows = [[
        'Data', 'Produto', 'Quantidade', 'Vendedor', 'Preço unit. (R$)', 'Custo unit. (R$)',
        'Comissão (%)', 'Receita (R$)', 'Custo (R$)', 'Comissão (R$)', 'Resultado (R$)',
    ]]
    total_units = 0
    for sale in products:
        total_units += sale.quantidade
        # entry = commissions[sale.barbeiro_id]
        # entry['units'] += sale.quantidade
        # entry['product_revenue'] += sale.valor_total
        # entry['product_commission'] += sale.comissao
        if sale.barbeiro_id is not None:
            entry = commissions[sale.barbeiro_id]
            entry['units'] += sale.quantidade
            entry['product_revenue'] += sale.valor_total
            entry['product_commission'] += sale.comissao
        excel_row = len(sale_rows) + 1
        sale_rows.append([
            # sale.data.isoformat(),
            # sale.produto.nome, 
            # sale.quantidade, 
            # sale.barbeiro.nome,
            sale.data.isoformat(),
            sale.produto.nome,
            sale.quantidade,
            sale.barbeiro.nome if sale.barbeiro_id else 'Barbearia',
            m(sale.preco_unitario), 
            m(sale.custo_unitario), 
            Percent(sale.percentual_comissao),
            m(sale.valor_total), m(sale.custo_total), m(sale.comissao),
            Formula(f'H{excel_row}-I{excel_row}-J{excel_row}',
                    sale.valor_total - sale.custo_total - sale.comissao),
        ])

    barber_rows = [[
        'Barbeiro', 'Serviços recebidos', 'Receita serviços (R$)', 'Comissão serviços (R$)',
        'Unidades vendidas', 'Receita produtos (R$)', 'Comissão produtos (R$)', 'Repasse total (R$)',
    ]]
    for b in barbers:
        x = commissions[b.pk]
        row_number = len(barber_rows) + 1
        barber_rows.append([
            b.nome, x['services'], m(x['service_revenue']), m(x['service_commission']),
            x['units'], m(x['product_revenue']), m(x['product_commission']),
            Formula(f'D{row_number}+G{row_number}', x['service_commission'] + x['product_commission']),
        ])

    expense_rows = [['Data', 'Descrição', 'Valor (R$)']]
    for expense in expenses:
        expense_rows.append([expense.data.isoformat(), expense.descricao, m(expense.valor)])

    received_revenue = d(balances['total_servicos'])
    product_revenue = d(balances['total_produtos'])
    revenue = d(balances['receita_bruta'])
    product_cost = d(balances['custo_produtos'])
    outgoings = d(balances['despesas'])
    service_comm = d(balances['comissoes_servicos'])
    product_comm = d(balances['comissoes_produtos'])
    total_comm = d(balances['comissoes'])
    owner_net = d(balances['saldo_proprietario'])

    def upto(rows):
        return max(2, len(rows))

    summary_rows = [
        ['Indicador', 'Valor'],
        ['Período', mes],
        ['Critério financeiro', 'Data efetiva do recebimento (caixa)'],
        ['Clientes agendados (únicos)', len({b.cliente_id for b in bookings})],
        ['Clientes atendidos (únicos)', len(unique_served_clients)],
        ['Agendamentos no período (inclusive cancelados)', len(bookings)],
        ['Serviços efetivamente recebidos', len(received)],
        ['Vendas de produtos (não estornadas)', len(products)],
        ['Unidades de produtos vendidas', total_units],
        ['Receita de serviços', Formula(f'SUM(Atendimentos!H2:H{upto(service_rows)})', received_revenue)],
        ['Receita de produtos', Formula(f'SUM(Vendas!H2:H{upto(sale_rows)})', product_revenue)],
        ['RECEITA BRUTA', Formula('B10+B11', revenue)],
        ['Custo de produtos', Formula(f'SUM(Vendas!I2:I{upto(sale_rows)})', product_cost)],
        ['Despesas', Formula(f'SUM(Despesas!C2:C{upto(expense_rows)})', outgoings)],
        ['Comissões de serviços', Formula(f'SUM(Atendimentos!J2:J{upto(service_rows)})', service_comm)],
        ['Comissões de produtos', Formula(f'SUM(Vendas!J2:J{upto(sale_rows)})', product_comm)],
        ['TOTAL DE COMISSÕES', Formula('B15+B16', total_comm)],
        ['LÍQUIDO DO PROPRIETÁRIO', Formula('B12-B13-B14-B17', owner_net)],
        ['Observação: agendamentos pendentes não compõem a receita.', ''],
        ['Observação: vendas de produtos não registram comprador no banco atual.', ''],
        ['Observação: tributos/taxas só entram se registrados como despesas.', ''],
        ['Fechado?', 'Sim' if balances['fechado'] else 'Não'],
    ]

    return workbook_bytes([
        ('Resumo', summary_rows, [65, 43], False),
        ('Atendimentos', service_rows, [18, 18, 12, 30, 20, 30, 26, 20, 17, 20, 24], True),
        ('Agendamentos', booking_rows, [18, 12, 30, 20, 29, 26, 16, 12, 23], True),
        ('Vendas', sale_rows, [18, 31, 15, 26, 23, 22, 18, 21, 21, 21, 22], True),
        ('Comissões', barber_rows, [28, 20, 25, 26, 22, 26, 27, 25], True),
        ('Despesas', expense_rows, [18, 48, 23], True),
    ])


class RelatorioExcelView(APIView):
    """Protegida pelos defaults de IsAdminUser e TokenAuthentication do projeto."""
    def get(self, request):
        mes = normalize_month(request.query_params.get('mes', timezone.localdate().strftime('%Y-%m')))
        payload = build_report(mes)
        response = HttpResponse(payload, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="Brenner_Relatorio_{mes}.xlsx"'
        response['Cache-Control'] = 'private, no-store'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
