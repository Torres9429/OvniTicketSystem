from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0008_alter_eventos_estatus'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventos',
            name='foto',
            field=models.TextField(blank=True, null=True),
        ),
    ]
