from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('barbeiros', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='Folga',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('data', models.DateField()),
                ('motivo', models.CharField(blank=True, max_length=180)),
                ('barbeiro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='folgas', to='barbeiros.barbeiro')),
            ],
            options={'ordering': ['data']},
        ),
        migrations.AddConstraint(
            model_name='folga', constraint=models.UniqueConstraint(fields=('barbeiro', 'data'), name='unique_barber_day_off')
        ),
    ]
