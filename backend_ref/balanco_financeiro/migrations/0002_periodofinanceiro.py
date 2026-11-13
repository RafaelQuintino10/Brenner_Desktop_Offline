from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('balanco_financeiro', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='PeriodoFinanceiro',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('mes', models.CharField(max_length=7, unique=True)),
                ('fechado', models.BooleanField(default=False)),
            ],
        ),
    ]
