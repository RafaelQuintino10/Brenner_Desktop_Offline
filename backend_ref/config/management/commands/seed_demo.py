from datetime import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from barbeiros.models import Barbeiro,HorarioBarbeiro
from agendamentos.models import Servico
from produtos.models import Produto
class Command(BaseCommand):
 help='Cria dados demonstrativos (idempotente). Não execute em produção.'
 def handle(self,*args,**kwargs):
  for nome,especialidade,c1,c2 in [('Matheus Brenner','Cortes modernos',45,12),('Lucas Pereira','Degradê e disfarçado',40,10),('Rafael Almeida','Barba e acabamento',42,10),('Diego Santos','Corte clássico',40,8)]:
   b,_=Barbeiro.objects.get_or_create(nome=nome,defaults={'especialidade':especialidade,'comissao_servico':c1,'comissao_produto':c2})
   for dia in range(6):
    for ini,fim in [(time(8,0),time(11,40)),(time(14,0),time(19,40))]:
     HorarioBarbeiro.objects.get_or_create(barbeiro=b,dia_semana=dia,inicio=ini,defaults={'fim':fim})
  for nome,preco,minutos in [('Corte Masculino','35.00',40),('Corte + Barba','55.00',60),('Barba','25.00',30),('Acabamento','15.00',20)]:
   Servico.objects.get_or_create(nome=nome,defaults={'preco':Decimal(preco),'duracao_minutos':minutos})
  products=[
   ('Pomada Modeladora Matte','Pomadas','49.90','21.00',24,'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=700&q=80'),
   ('Óleo para Barba Premium','Barba','39.90','16.00',18,'https://images.unsplash.com/photo-1621607512214-68297480165e?w=700&q=80'),
   ('Shampoo Masculino 300ml','Shampoos','34.90','14.00',32,'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=700&q=80'),
   ('Loção Pós-Barba','Loções','42.00','19.00',12,'https://images.unsplash.com/photo-1594035910387-fea47794261f?w=700&q=80'),
   ('Cera Modeladora Strong','Pomadas','55.00','24.00',14,'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=700&q=80')]
  for n,c,p,cost,stock,img in products:
   Produto.objects.get_or_create(nome=n,defaults={'categoria':c,'preco':Decimal(p),'custo':Decimal(cost),'estoque':stock,'imagem_url':img,'descricao':'Produto para cuidar do seu estilo em casa.'})
  self.stdout.write(self.style.SUCCESS('Dados demonstrativos carregados.'))
