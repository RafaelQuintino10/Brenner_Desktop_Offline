from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('vendas', '0001_initial')]
    operations = [
        migrations.AddField(model_name='venda', name='estornada', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='venda', name='estornada_em', field=models.DateTimeField(null=True, blank=True)),
    ]
