from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('agendamentos', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='agendamento', name='duracao_minutos',
            field=models.PositiveSmallIntegerField(default=40),
        ),
    ]
