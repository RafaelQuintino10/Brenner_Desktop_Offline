
"""Executar em backend: python manage.py test tests.test_relatorio_excel"""
from datetime import time
from decimal import Decimal
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from barbeiros.models import Barbeiro
from agendamentos.models import Agendamento, Cliente, Servico
from produtos.models import Produto
from vendas.models import Venda, VendaServico
from balanco_financeiro.models import Despesa


NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


class RelatorioExcelTests(TestCase):
    def setUp(self):
        self.admin = APIClient()
        self.public = APIClient()
        user = get_user_model().objects.create_superuser('brenner-teste', 'teste@brenner.local', 'senha-forte-testes')
        self.admin.force_authenticate(user=user)
        self.date = timezone.localdate()
        self.mes = self.date.strftime('%Y-%m')
        barber = Barbeiro.objects.create(nome='Carlos Silva', comissao_servico=40, comissao_produto=10)
        client = Cliente.objects.create(nome='João Silva', telefone='88999999999')
        service = Servico.objects.create(nome='Corte + Barba', preco='50.00', duracao_minutos=45)
        appointment = Agendamento.objects.create(
            cliente=client, barbeiro=barber, servico=service, data=self.date, hora=time(10),
            status='concluido', pago=True, valor_cobrado=Decimal('50.00'),
        )
        VendaServico.objects.create(
            agendamento=appointment, barbeiro=barber, data=self.date,
            valor=Decimal('50.00'), percentual_comissao=Decimal('40.00'), comissao=Decimal('20.00'),
        )
        product = Produto.objects.create(nome='Pomada', categoria='Pomadas', preco='30.00', custo='12.00', estoque=7)
        Venda.objects.create(
            produto=product, barbeiro=barber, data=self.date, quantidade=2,
            preco_unitario=Decimal('30.00'), custo_unitario=Decimal('12.00'),
            percentual_comissao=Decimal('10.00'), valor_total=Decimal('60.00'),
            custo_total=Decimal('24.00'), comissao=Decimal('6.00'),
        )
        Despesa.objects.create(descricao='Material', data=self.date, valor=Decimal('10.00'))

    @staticmethod
    def cell_value(sheet_xml, address):
        root = ET.fromstring(sheet_xml)
        cell = root.find(f'.//m:c[@r="{address}"]', NS)
        assert cell is not None, address
        numeric = cell.find('m:v', NS)
        if numeric is not None:
            return numeric.text
        t = cell.find('m:is/m:t', NS)
        return t.text if t is not None else None

    def test_admin_downloads_accurate_report(self):
        response = self.admin.get(f'/api/financeiro/excel/?mes={self.mes}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml.sheet', response['Content-Type'])
        with ZipFile(BytesIO(response.content)) as book:
            self.assertIsNone(book.testzip())
            workbook = book.read('xl/workbook.xml').decode('utf-8')
            for name in ['Resumo', 'Atendimentos', 'Agendamentos', 'Vendas', 'Comissões', 'Despesas']:
                self.assertIn(f'name="{name}"', workbook)
            resumo = book.read('xl/worksheets/sheet1.xml')
            self.assertEqual(self.cell_value(resumo, 'B5'), '1')  # cliente atendido único
            self.assertEqual(self.cell_value(resumo, 'B12'), '110.00')  # receita bruta
            self.assertEqual(self.cell_value(resumo, 'B17'), '26.00')  # comissões totais
            self.assertEqual(self.cell_value(resumo, 'B18'), '50.00')  # liquido proprietário
            self.assertEqual(self.cell_value(book.read('xl/worksheets/sheet2.xml'), 'D2'), 'João Silva')
            self.assertEqual(self.cell_value(book.read('xl/worksheets/sheet4.xml'), 'B2'), 'Pomada')

    def test_unauthenticated_cannot_download_personal_data(self):
        response = self.public.get(f'/api/financeiro/excel/?mes={self.mes}')
        self.assertIn(response.status_code, (401, 403))

    def test_invalid_month_is_rejected(self):
        response = self.admin.get('/api/financeiro/excel/?mes=2026-99')
        self.assertEqual(response.status_code, 400)
