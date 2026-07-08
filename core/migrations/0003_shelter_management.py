from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_waterlevel_api_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmergencyShelter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('shelter_type', models.CharField(choices=[('SCHOOL', 'School / College'), ('COMMUNITY', 'Community Hall'), ('TEMPLE', 'Temple / Church / Mosque'), ('GOVT', 'Government Building'), ('STADIUM', 'Stadium / Sports Complex'), ('OTHER', 'Other')], default='SCHOOL', max_length=30)),
                ('district', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('total_capacity', models.IntegerField(default=100)),
                ('current_occupancy', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('FULL', 'Full'), ('CLOSED', 'Closed'), ('STANDBY', 'Standby')], default='OPEN', max_length=20)),
                ('contact_person', models.CharField(blank=True, max_length=200)),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('has_medical', models.BooleanField(default=False)),
                ('has_food', models.BooleanField(default=True)),
                ('has_water', models.BooleanField(default=True)),
                ('has_power', models.BooleanField(default=False)),
                ('has_toilets', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_teams', models.ManyToManyField(blank=True, related_name='assigned_shelters', to='core.rescueteam')),
            ],
            options={'verbose_name': 'Emergency Shelter', 'verbose_name_plural': 'Emergency Shelters', 'ordering': ['district', 'name']},
        ),
        migrations.CreateModel(
            name='DisplacedPerson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shelter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='persons', to='core.emergencyshelter')),
                ('name', models.CharField(max_length=200)),
                ('age', models.IntegerField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('home_address', models.TextField(blank=True)),
                ('home_district', models.CharField(blank=True, max_length=100)),
                ('family_size', models.IntegerField(default=1)),
                ('needs_medical', models.BooleanField(default=False)),
                ('medical_notes', models.TextField(blank=True)),
                ('checked_in_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('checked_out_at', models.DateTimeField(blank=True, null=True)),
                ('checked_in_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='checkins', to=settings.AUTH_USER_MODEL)),
                ('notes', models.TextField(blank=True)),
            ],
            options={'verbose_name': 'Displaced Person', 'verbose_name_plural': 'Displaced Persons', 'ordering': ['-checked_in_at']},
        ),
    ]
