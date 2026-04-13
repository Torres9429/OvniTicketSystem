from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordenes', '0002_alter_ordenes_estatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordenes',
            name='operation_id',
            field=models.CharField(blank=True, db_column='operation_id', db_index=True, max_length=64, null=True, unique=True),
        ),
    ]
