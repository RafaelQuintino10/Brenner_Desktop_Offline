"""Integração real via Django test client e banco PostgreSQL de teste."""
from datetime import date, time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from barbeiros.models import Barbeiro, HorarioBarbeiro, Folga
from agendamentos.models import Servico, Agendamento
from produtos.models import Produto
from vendas.models import Venda, VendaServico
from balanco_financeiro.models import Fechamento


class BackendTests(TestCase):
    def setUp(self):
        self.barbeiro = Barbeiro.objects.create(
            nome='Carlos', comissao_servico=Decimal('40'), comissao_produto=Decimal('10')
        )
        self.servico = Servico.objects.create(nome='Corte', preco=Decimal('50.00'), duracao_minutos=40)
        self.produto = Produto.objects.create(nome='Pomada', preco=Decimal('30.00'), custo=Decimal('12.00'), estoque=3)
        self.dia = timezone.localdate() + timedelta(days=7)
        HorarioBarbeiro.objects.create(barbeiro=self.barbeiro, dia_semana=self.dia.weekday(), inicio=time(8), fim=time(12))
        self.public = APIClient()
        self.admin = APIClient()
        user = get_user_model().objects.create_superuser('admin-test', 'admin@test.local', 'senha-segura-teste')
        token = Token.objects.create(user=user)
        self.admin.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def booking_data(self, hora='09:00'):
        return {
            'cliente_nome': 'José Teste', 'cliente_telefone': '88999999999',
            'barbeiro': self.barbeiro.id, 'servico': self.servico.id,
            'data': self.dia.isoformat(), 'hora': hora,
        }

    def make_booking(self):
        response = self.public.post('/api/public/agendamentos/', self.booking_data(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_public_catalog_omits_private_data_and_contains_whatsapp(self):
        data = self.public.get('/api/public/catalogo/').data
        self.assertNotIn('custo', data['produtos'][0])
        self.assertNotIn('comissao_servico', data['barbeiros'][0])
        self.assertTrue(data['produtos'][0]['whatsapp_url'].startswith('https://wa.me/'))

    def test_public_booking_appears_in_admin_and_conflicts_are_rejected(self):
        self.make_booking()
        second = self.public.post('/api/public/agendamentos/', self.booking_data('09:20'), format='json')
        self.assertEqual(second.status_code, 400, second.data)
        listing = self.admin.get('/api/agendamentos/')
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.data['count'], 1)
        self.assertEqual(Agendamento.objects.first().duracao_minutos, 40)

    def test_availability_respects_duration_and_occupied_slots(self):
        self.make_booking()
        url = f'/api/public/disponibilidade/?barbeiro={self.barbeiro.pk}&servico={self.servico.pk}&data={self.dia}'
        response = self.public.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('09:00', response.data['horarios'])
        self.assertNotIn('09:20', response.data['horarios'])
        self.assertIn('10:00', response.data['horarios'])

    def test_folga_blocks_booking(self):
        Folga.objects.create(barbeiro=self.barbeiro, data=self.dia)
        self.assertEqual(
            self.public.post('/api/public/agendamentos/', self.booking_data(), format='json').status_code, 400
        )

    def test_cannot_create_folga_while_booking_exists(self):
        self.make_booking()
        response = self.admin.post('/api/folgas/', {'barbeiro': self.barbeiro.pk, 'data': self.dia.isoformat()})
        self.assertEqual(response.status_code, 400)

    def test_paid_booking_uses_receipt_date_and_freezes_commission(self):
        booking_id = self.make_booking()
        response = self.admin.patch(
            f'/api/agendamentos/{booking_id}/', {'status': 'concluido', 'pago': True}, format='json'
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(VendaServico.objects.count(), 1)
        row = VendaServico.objects.get()
        self.assertEqual(row.data, timezone.localdate())
        self.assertEqual(row.comissao, Decimal('20.00'))
        self.barbeiro.comissao_servico = Decimal('75')
        self.barbeiro.save(update_fields=['comissao_servico'])
        row.refresh_from_db()
        self.assertEqual(row.comissao, Decimal('20.00'))
        again = self.admin.patch(f'/api/agendamentos/{booking_id}/', {'pago': True}, format='json')
        self.assertEqual(again.status_code, 400)
        self.assertEqual(VendaServico.objects.count(), 1)

    def test_product_sale_stock_commission_and_refund(self):
        response = self.admin.post(
            '/api/vendas/', {'produto': self.produto.id, 'barbeiro': self.barbeiro.id, 'quantidade': 2}, format='json'
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 1)
        sale = Venda.objects.get()
        self.assertEqual(sale.valor_total, Decimal('60.00'))
        self.assertEqual(sale.custo_total, Decimal('24.00'))
        self.assertEqual(sale.comissao, Decimal('6.00'))
        refused = self.admin.post('/api/vendas/', {
            'produto': self.produto.pk, 'barbeiro': self.barbeiro.pk, 'quantidade': 2,
        }, format='json')
        self.assertEqual(refused.status_code, 400)
        refund = self.admin.post(f'/api/vendas/{sale.pk}/estornar/', {}, format='json')
        self.assertEqual(refund.status_code, 200, refund.data)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque, 3)
        self.assertEqual(self.admin.post(f'/api/vendas/{sale.pk}/estornar/', {}, format='json').status_code, 400)

    def test_summary_receipts_costs_commissions_and_expenses(self):
        self.make_booking()
        booking = Agendamento.objects.get()
        r = self.admin.patch(f'/api/agendamentos/{booking.pk}/', {'status': 'concluido', 'pago': True}, format='json')
        self.assertEqual(r.status_code, 200, r.data)
        sale = self.admin.post('/api/vendas/', {
            'produto': self.produto.pk, 'barbeiro': self.barbeiro.pk, 'quantidade': 2,
        }, format='json')
        self.assertEqual(sale.status_code, 201, sale.data)
        expense = self.admin.post('/api/despesas/', {
            'descricao': 'Aluguel proporcional', 'data': str(timezone.localdate()), 'valor': '10.00',
        }, format='json')
        self.assertEqual(expense.status_code, 201, expense.data)
        mes = timezone.localdate().strftime('%Y-%m')
        resumo = self.admin.get(f'/api/financeiro/resumo/?mes={mes}').data
        self.assertEqual(resumo['receita_bruta'], '110.00')
        self.assertEqual(resumo['custo_produtos'], '24.00')
        self.assertEqual(resumo['comissoes'], '26.00')
        self.assertEqual(resumo['saldo_proprietario'], '50.00')
        self.assertEqual(resumo['repasses'][0]['total'], '26.00')

    def test_closed_month_cannot_receive_new_sales(self):
        last_month = timezone.localdate().replace(day=1) - timedelta(days=1)
        before = self.admin.post('/api/vendas/', {
            'produto': self.produto.pk, 'barbeiro': self.barbeiro.pk,
            'quantidade': 1, 'data': str(last_month),
        }, format='json')
        self.assertEqual(before.status_code, 201, before.data)
        mes = last_month.strftime('%Y-%m')
        close = self.admin.post('/api/financeiro/fechamentos/', {'mes': mes}, format='json')
        self.assertEqual(close.status_code, 201, close.data)
        self.assertTrue(Fechamento.objects.filter(mes=mes).exists())
        blocked = self.admin.post('/api/vendas/', {
            'produto': self.produto.pk, 'barbeiro': self.barbeiro.pk,
            'quantidade': 1, 'data': str(last_month),
        }, format='json')
        self.assertEqual(blocked.status_code, 400)
        self.assertEqual(self.admin.post(f"/api/vendas/{before.data['id']}/estornar/", {}, format='json').status_code, 400)

    def test_cannot_close_current_month(self):
        r = self.admin.post('/api/financeiro/fechamentos/', {'mes': timezone.localdate().strftime('%Y-%m')}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_api_is_private_except_public_endpoints(self):
        self.assertIn(self.public.get('/api/produtos/').status_code, (401, 403))
        self.assertEqual(self.public.get('/api/public/produtos/').status_code, 200)
        self.assertIn(self.public.get('/api/financeiro/resumo/').status_code, (401, 403))

    def test_product_commission_percentage_validation(self):
        r = self.admin.patch(f'/api/barbeiros/{self.barbeiro.id}/', {'comissao_produto': '150.00'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_health_uses_postgres(self):
        r = self.public.get('/api/health/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['database'], 'postgresql')
