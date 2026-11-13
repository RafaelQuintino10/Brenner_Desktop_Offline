from django.db import migrations,models
import django.core.validators
class Migration(migrations.Migration):
 initial=True;dependencies=[]
 operations=[
  migrations.CreateModel(name='Despesa',fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('descricao',models.CharField(max_length=200)),('data',models.DateField()),('valor',models.DecimalField(max_digits=12,decimal_places=2,validators=[django.core.validators.MinValueValidator(0.01)])),('criado_em',models.DateTimeField(auto_now_add=True))],options={'ordering':['-data']}),
  migrations.CreateModel(name='Fechamento',fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('mes',models.CharField(max_length=7,unique=True)),('total_servicos',models.DecimalField(max_digits=12,decimal_places=2)),('total_produtos',models.DecimalField(max_digits=12,decimal_places=2)),('custo_produtos',models.DecimalField(max_digits=12,decimal_places=2)),('despesas',models.DecimalField(max_digits=12,decimal_places=2)),('comissoes',models.DecimalField(max_digits=12,decimal_places=2)),('saldo_proprietario',models.DecimalField(max_digits=12,decimal_places=2)),('repasses',models.JSONField(default=list)),('fechado_em',models.DateTimeField(auto_now_add=True))])]
