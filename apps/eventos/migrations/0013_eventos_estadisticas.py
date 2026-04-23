from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0012_create_mysql_triggers'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventos',
            name='boletos_vendidos',
            field=models.IntegerField(default=0, db_column='boletos_vendidos'),
        ),
        migrations.AddField(
            model_name='eventos',
            name='ingresos_totales',
            field=models.FloatField(default=0.0, db_column='ingresos_totales'),
        ),
        migrations.AddField(
            model_name='eventos',
            name='ocupacion_pct',
            field=models.FloatField(default=0.0, db_column='ocupacion_pct'),
        ),
    ]
