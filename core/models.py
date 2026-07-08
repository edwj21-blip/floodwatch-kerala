from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class WaterLevel(models.Model):
    LEVEL_CHOICES = [
        ('NORMAL', 'Normal'),
        ('WATCH', 'Watch'),
        ('WARNING', 'Warning'),
        ('DANGER', 'Danger'),
        ('CRITICAL', 'Critical'),
    ]

    location_name = models.CharField(max_length=200)
    district = models.CharField(max_length=100)
    current_level_meters = models.FloatField(help_text="Water level in meters")
    danger_level_meters = models.FloatField(help_text="Danger threshold in meters")
    warning_level_meters = models.FloatField(help_text="Warning threshold in meters")
    status = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='NORMAL')
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ── Weather / API fields ────────────────────────────────────────────────
    rainfall_mm = models.FloatField(default=0.0, help_text="Rainfall in last hour (mm) from API")
    temperature_c = models.FloatField(default=28.0, help_text="Current temperature °C")
    humidity_pct = models.FloatField(default=70.0, help_text="Relative humidity %")
    weather_description = models.CharField(max_length=200, blank=True, help_text="e.g. heavy rain")
    rainfall_accuracy_pct = models.FloatField(default=0.0, help_text="Rainfall accuracy % (0-100)")
    weather_icon = models.CharField(max_length=20, blank=True)
    api_last_synced = models.DateTimeField(null=True, blank=True, help_text="Last weather API sync time")

    class Meta:
        ordering = ['-last_updated']
        verbose_name = "Water Level Monitor"
        verbose_name_plural = "Water Level Monitors"

    def __str__(self):
        return f"{self.location_name} - {self.current_level_meters}m ({self.status})"

    def get_percentage(self):
        if self.danger_level_meters > 0:
            pct = (self.current_level_meters / self.danger_level_meters) * 100
            return min(int(pct), 100)
        return 0

    def save(self, *args, **kwargs):
        # Auto-compute status from current vs threshold
        if self.current_level_meters >= self.danger_level_meters:
            self.status = 'CRITICAL'
        elif self.current_level_meters >= self.danger_level_meters * 0.85:
            self.status = 'DANGER'
        elif self.current_level_meters >= self.warning_level_meters:
            self.status = 'WARNING'
        elif self.current_level_meters >= self.warning_level_meters * 0.75:
            self.status = 'WATCH'
        else:
            self.status = 'NORMAL'
        super().save(*args, **kwargs)


class FloodAlert(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('EXTREME', 'Extreme'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField()
    affected_area = models.CharField(max_length=300)
    district = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    is_active = models.BooleanField(default=True)
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    water_level = models.ForeignKey(WaterLevel, on_delete=models.SET_NULL, null=True, blank=True)
    auto_generated = models.BooleanField(default=False, help_text="Auto-created by weather sync")

    class Meta:
        ordering = ['-issued_at']
        verbose_name = "Flood Alert"
        verbose_name_plural = "Flood Alerts"

    def __str__(self):
        return f"[{self.severity}] {self.title} - {self.affected_area}"


class RescueTeam(models.Model):
    name = models.CharField(max_length=200)
    team_type = models.CharField(max_length=100, choices=[
        ('NDRF', 'NDRF - National Disaster Response Force'),
        ('SDRF', 'SDRF - State Disaster Response Force'),
        ('FIRE', 'Fire & Rescue Services'),
        ('COAST_GUARD', 'Coast Guard'),
        ('POLICE', 'Police Emergency'),
        ('HEALTH', 'Health & Medical'),
        ('CIVIL', 'Civil Defence'),
        ('NGO', 'NGO / Volunteer Group'),
        ('OTHER', 'Other'),
    ])
    contact_number = models.CharField(max_length=20)
    alternate_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    district = models.CharField(max_length=100)
    base_location = models.CharField(max_length=200)
    is_available = models.BooleanField(default=True)
    personnel_count = models.IntegerField(default=0)
    vehicles_available = models.IntegerField(default=0)
    boats_available = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['district', 'name']
        verbose_name = "Rescue Team"
        verbose_name_plural = "Rescue Teams"

    def __str__(self):
        return f"{self.name} ({self.district}) - {self.contact_number}"


class FloodReport(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('VERIFIED', 'Verified'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected'),
    ]

    SEVERITY_CHOICES = [
        ('MINOR', 'Minor'),
        ('MODERATE', 'Moderate'),
        ('SEVERE', 'Severe'),
        ('CATASTROPHIC', 'Catastrophic'),
    ]

    reporter_name = models.CharField(max_length=200)
    reporter_phone = models.CharField(max_length=20)
    reporter_email = models.EmailField(blank=True)
    location = models.CharField(max_length=300)
    district = models.CharField(max_length=100)
    description = models.TextField()
    water_level_estimate = models.CharField(max_length=100, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MODERATE')
    photo = models.ImageField(upload_to='reports/%Y/%m/', null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reported_at = models.DateTimeField(default=timezone.now)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    admin_notes = models.TextField(blank=True)
    rescue_team_assigned = models.ForeignKey(RescueTeam, on_delete=models.SET_NULL, null=True, blank=True)
    people_affected = models.IntegerField(default=0)
    evacuation_needed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-reported_at']
        verbose_name = "Flood Report"
        verbose_name_plural = "Flood Reports"

    def __str__(self):
        return f"{self.reporter_name} - {self.location} ({self.reported_at.strftime('%d %b %Y')})"


class EmergencyContact(models.Model):
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=200)
    department = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    district = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Emergency Contact"
        verbose_name_plural = "Emergency Contacts"

    def __str__(self):
        return f"{self.name} - {self.designation}"


# ─── Shelter Management ───────────────────────────────────────────────────────

class EmergencyShelter(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('FULL', 'Full'),
        ('CLOSED', 'Closed'),
        ('STANDBY', 'Standby'),
    ]

    SHELTER_TYPE_CHOICES = [
        ('SCHOOL', 'School / College'),
        ('COMMUNITY', 'Community Hall'),
        ('TEMPLE', 'Temple / Church / Mosque'),
        ('GOVT', 'Government Building'),
        ('STADIUM', 'Stadium / Sports Complex'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=300)
    shelter_type = models.CharField(max_length=30, choices=SHELTER_TYPE_CHOICES, default='SCHOOL')
    district = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    total_capacity = models.IntegerField(default=100, help_text="Maximum number of people")
    current_occupancy = models.IntegerField(default=0, help_text="Current number of displaced persons")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    contact_person = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)

    has_medical = models.BooleanField(default=False, help_text="Medical facility available")
    has_food = models.BooleanField(default=True, help_text="Food provided")
    has_water = models.BooleanField(default=True, help_text="Clean water available")
    has_power = models.BooleanField(default=False, help_text="Generator / power backup")
    has_toilets = models.BooleanField(default=True)

    assigned_teams = models.ManyToManyField(
        RescueTeam, blank=True, related_name='assigned_shelters',
        help_text="Rescue teams assigned to this shelter"
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['district', 'name']
        verbose_name = "Emergency Shelter"
        verbose_name_plural = "Emergency Shelters"

    def __str__(self):
        return f"{self.name} ({self.district}) — {self.current_occupancy}/{self.total_capacity}"

    def available_capacity(self):
        return max(0, self.total_capacity - self.current_occupancy)

    def occupancy_pct(self):
        if self.total_capacity > 0:
            return min(100, int((self.current_occupancy / self.total_capacity) * 100))
        return 0

    def save(self, *args, **kwargs):
        # Auto-update status based on occupancy
        if self.status not in ('CLOSED', 'STANDBY'):
            if self.current_occupancy >= self.total_capacity:
                self.status = 'FULL'
            else:
                self.status = 'OPEN'
        super().save(*args, **kwargs)


class DisplacedPerson(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    shelter = models.ForeignKey(EmergencyShelter, on_delete=models.CASCADE, related_name='persons')
    name = models.CharField(max_length=200)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    home_address = models.TextField(blank=True)
    home_district = models.CharField(max_length=100, blank=True)
    family_size = models.IntegerField(default=1, help_text="Number of family members checked in together")
    needs_medical = models.BooleanField(default=False)
    medical_notes = models.TextField(blank=True)
    checked_in_at = models.DateTimeField(default=timezone.now)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='checkins'
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-checked_in_at']
        verbose_name = "Displaced Person"
        verbose_name_plural = "Displaced Persons"

    def __str__(self):
        return f"{self.name} @ {self.shelter.name}"

    @property
    def is_checked_in(self):
        return self.checked_out_at is None
