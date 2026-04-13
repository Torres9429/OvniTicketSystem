from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zonas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='zonas',
            name='precio',
            field=models.FloatField(default=0),
        ),
    ]
