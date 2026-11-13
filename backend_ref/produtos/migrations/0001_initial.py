from django.db import migrations,models
import django.core.validators
class Migration(migrations.Migration):
 initial=True;dependencies=[]
 operations=[migrations.CreateModel(name='Produto',fields=[('id',models.BigAutoField(primary_key=True,serialize=False)),('nome',models.CharField(max_length=150)),('categoria',models.CharField(max_length=70,default='Outros')),('descricao',models.TextField(blank=True)),('preco',models.DecimalField(max_digits=10,decimal_places=2,validators=[django.core.validators.MinValueValidator(0)])),('custo',models.DecimalField(max_digits=10,decimal_places=2,default=0,validators=[django.core.validators.MinValueValidator(0)])),('estoque',models.PositiveIntegerField(default=0)),('estoque_minimo',models.PositiveIntegerField(default=5)),('imagem_url',models.URLField(blank=True)),('ativo',models.BooleanField(default=True))],options={'ordering':['nome']})]
