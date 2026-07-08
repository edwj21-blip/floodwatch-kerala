from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='waterlevel',
            name='rainfall_mm',
            field=models.FloatField(default=0.0, help_text='Rainfall in last hour (mm) from API'),
        ),
        migrations.AddField(
            model_name='waterlevel',
            name='temperature_c',
            field=models.FloatField(default=28.0, help_text='Current temperature °C'),
        ),
        migrations.AddField(
            model_name='waterlevel',
            name='humidity_pct',
            field=models.FloatField(default=70.0, help_text='Relative humidity %'),
        ),
        migrations.AddField(
            model_name='waterlevel',
            name='weather_description',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='waterlevel',
            name='rainfall_accuracy_pct',
            field=models.FloatField(default=0.0, help_text='Rainfall accuracy % (0-100)'),
        ),
        migrations.AddField(
            model_name='waterlevel',
            name='weather_icon',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='waterlevel',
            name='api_last_synced',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='floodalert',
            name='auto_generated',
            field=models.BooleanField(default=False, help_text='Auto-created by weather sync'),
        ),
    ]
