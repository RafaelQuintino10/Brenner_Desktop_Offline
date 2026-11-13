from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
class Migration(migrations.Migration):
 initial=True
 dependencies=[]
 operations=[
  migrations.CreateModel(name='Barbeiro',fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('nome',models.CharField(max_length=120)),('telefone',models.CharField(max_length=22,blank=True)),('especialidade',models.CharField(max_length=120,default='Corte masculino')),('comissao_servico',models.DecimalField(max_digits=5,decimal_places=2,default=40,validators=[django.core.validators.MinValueValidator(0),django.core.validators.MaxValueValidator(100)])),('comissao_produto',models.DecimalField(max_digits=5,decimal_places=2,default=10,validators=[django.core.validators.MinValueValidator(0),django.core.validators.MaxValueValidator(100)])),('ativo',models.BooleanField(default=True)),('foto_url',models.URLField(blank=True))],options={'ordering':['nome']}),
  migrations.CreateModel(name='HorarioBarbeiro',fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('dia_semana',models.PositiveSmallIntegerField(choices=[(0,'Segunda'),(1,'Terça'),(2,'Quarta'),(3,'Quinta'),(4,'Sexta'),(5,'Sábado'),(6,'Domingo')])),('inicio',models.TimeField()),('fim',models.TimeField()),('barbeiro',models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name='horarios',to='barbeiros.barbeiro'))],options={'ordering':['dia_semana','inicio'],'unique_together':{('barbeiro','dia_semana','inicio')}})
 ]
