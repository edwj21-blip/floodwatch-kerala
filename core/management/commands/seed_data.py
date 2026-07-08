from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import WaterLevel, FloodAlert, RescueTeam, EmergencyContact


class Command(BaseCommand):
    help = 'Seeds the database with FloodWatch Kerala data (all 14 districts)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌊 Seeding FloodWatch database...')

        # Admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@floodwatch.in', 'admin123')
            self.stdout.write('✅ Admin user: admin / admin123')

        # Regular user
        if not User.objects.filter(username='user1').exists():
            u = User.objects.create_user('user1', 'user1@example.com', 'user123')
            self.stdout.write('✅ Regular user: user1 / user123')

        user = User.objects.get(username='admin')

        # Water Levels (all 14 districts)
        WaterLevel.objects.all().delete()
        water_data = [
            ('Periyar River - Aluva', 'Ernakulam', 8.4, 10.0, 7.5),
            ('Pampa River - Thiruvalla', 'Pathanamthitta', 9.2, 10.5, 8.0),
            ('Chaliyar River - Malappuram', 'Malappuram', 5.1, 9.0, 6.5),
            ('Bharathapuzha - Palakkad', 'Palakkad', 11.3, 12.0, 9.0),
            ('Kabani River - Wayanad', 'Wayanad', 3.8, 8.0, 6.0),
            ('Kallada River - Kollam', 'Kollam', 4.2, 7.5, 5.5),
            ('Achankovil - Pathanamthitta', 'Pathanamthitta', 2.9, 6.0, 4.5),
            ('Valapattanam River - Kannur', 'Kannur', 6.7, 8.5, 6.0),
            ('Meenachil River - Kottayam', 'Kottayam', 3.5, 6.5, 5.0),
            ('Muvattupuzha River - Ernakulam', 'Ernakulam', 5.8, 8.0, 6.0),
            ('Pamba at Alappuzha', 'Alappuzha', 2.1, 3.5, 2.5),
            ('Mananthavady River - Wayanad', 'Wayanad', 4.9, 7.0, 5.5),
            ('Kallayi River - Kozhikode', 'Kozhikode', 3.2, 5.0, 3.8),
            ('Karyangode River - Kasaragod', 'Kasaragod', 2.8, 5.5, 4.0),
        ]
        for name, district, current, danger, warning in water_data:
            wl = WaterLevel(
                location_name=name, district=district,
                current_level_meters=current, danger_level_meters=danger,
                warning_level_meters=warning,
                notes=f'Monitoring station at {name}'
            )
            wl.save()
        self.stdout.write(f'✅ Created {len(water_data)} water level monitors')

        # Flood Alerts
        FloodAlert.objects.all().delete()
        alerts_data = [
            ('Red Alert: Bharathapuzha Overflow Risk', 'Palakkad', 'HIGH', 'Palakkad, Thrissur districts', 'River level dangerously close to danger mark. Residents near banks advised to evacuate immediately.'),
            ('Orange Alert: Pampa River Rising', 'Pathanamthitta', 'MEDIUM', 'Thiruvalla, Ranni, Konni', 'Pampa river water level rising due to heavy rainfall. Low-lying areas to remain alert.'),
            ('Flash Flood Warning: Wayanad', 'Wayanad', 'EXTREME', 'Mananthavady, Kalpetta, Sulthan Bathery', 'Extreme rainfall triggering flash floods. Immediate evacuation of tribal settlements in hilly areas ordered.'),
            ('Yellow Alert: Ernakulam Waterlogging', 'Ernakulam', 'LOW', 'Aluva, Perumbavoor, North Paravur', 'Waterlogging reported in low-lying areas. Traffic disruption expected. Residents advised caution.'),
        ]
        for title, district, severity, area, desc in alerts_data:
            FloodAlert.objects.create(
                title=title, district=district, severity=severity,
                affected_area=area, description=desc,
                is_active=True, issued_by=user,
                expires_at=timezone.now() + timedelta(hours=24)
            )
        self.stdout.write(f'✅ Created {len(alerts_data)} flood alerts')

        # Rescue Teams — all 14 districts
        RescueTeam.objects.all().delete()
        teams_data = [
            ('NDRF Battalion 7', 'NDRF', '0484-2660501', 'Ernakulam', 'Aluva', True, 45, 8, 12),
            ('Kerala Fire & Rescue - Thrissur', 'FIRE', '0487-2332222', 'Thrissur', 'Thrissur City', True, 30, 6, 5),
            ('SDRF Palakkad Unit', 'SDRF', '0491-2505050', 'Palakkad', 'Palakkad Town', True, 25, 4, 3),
            ('Kerala Fire & Rescue - Wayanad', 'FIRE', '04936-202900', 'Wayanad', 'Kalpetta', True, 20, 3, 2),
            ('Coast Guard Station Kochi', 'COAST_GUARD', '0484-2666685', 'Ernakulam', 'Kochi Port', True, 60, 4, 8),
            ('SDRF Kollam Unit', 'SDRF', '0474-2743333', 'Kollam', 'Kollam Town', True, 20, 3, 2),
            ('Fire & Rescue - Thiruvananthapuram', 'FIRE', '0471-2721100', 'Thiruvananthapuram', 'Tvpm City', True, 35, 7, 4),
            ('NDRF - Pathanamthitta', 'NDRF', '0468-2322222', 'Pathanamthitta', 'Thiruvalla', True, 30, 5, 6),
            ('Coast Guard - Alappuzha', 'COAST_GUARD', '0477-2263580', 'Alappuzha', 'Alappuzha Town', True, 40, 3, 10),
            ('Fire & Rescue - Kottayam', 'FIRE', '0481-2568881', 'Kottayam', 'Kottayam Town', True, 22, 4, 3),
            ('SDRF - Idukki', 'SDRF', '0486-2232100', 'Idukki', 'Painavu', True, 18, 2, 2),
            ('Fire & Rescue - Malappuram', 'FIRE', '0483-2766100', 'Malappuram', 'Malappuram Town', True, 25, 4, 2),
            ('SDRF - Kozhikode', 'SDRF', '0495-2365500', 'Kozhikode', 'Calicut City', True, 28, 5, 4),
            ('Fire & Rescue - Kannur', 'FIRE', '0497-2700101', 'Kannur', 'Kannur Town', True, 24, 4, 3),
            ('SDRF - Kasaragod', 'SDRF', '0499-4255700', 'Kasaragod', 'Kasaragod Town', True, 16, 3, 2),
            ('Medical Emergency - DMER', 'HEALTH', '0471-2443900', 'Thiruvananthapuram', 'State HQ', True, 50, 10, 0),
            ('Civil Defence - Ernakulam', 'CIVIL', '0484-2350000', 'Ernakulam', 'Kochi', True, 100, 5, 0),
        ]
        for name, ttype, phone, district, base, avail, personnel, vehicles, boats in teams_data:
            RescueTeam.objects.create(
                name=name, team_type=ttype, contact_number=phone,
                district=district, base_location=base, is_available=avail,
                personnel_count=personnel, vehicles_available=vehicles, boats_available=boats
            )
        self.stdout.write(f'✅ Created {len(teams_data)} rescue teams')

        # Emergency Contacts — all 14 districts
        EmergencyContact.objects.all().delete()
        contacts_data = [
            ('District Collector', 'Collector', 'Revenue — Thiruvananthapuram', '0471-2320182', 'Thiruvananthapuram'),
            ('District Collector', 'Collector', 'Revenue — Kollam', '0474-2745606', 'Kollam'),
            ('District Collector', 'Collector', 'Revenue — Pathanamthitta', '0468-2323001', 'Pathanamthitta'),
            ('District Collector', 'Collector', 'Revenue — Alappuzha', '0477-2253501', 'Alappuzha'),
            ('District Collector', 'Collector', 'Revenue — Kottayam', '0481-2560101', 'Kottayam'),
            ('District Collector', 'Collector', 'Revenue — Idukki', '0486-2232225', 'Idukki'),
            ('District Collector', 'Collector', 'Revenue — Ernakulam', '0484-2423001', 'Ernakulam'),
            ('District Collector', 'Collector', 'Revenue — Thrissur', '0487-2322555', 'Thrissur'),
            ('District Collector', 'Collector', 'Revenue — Palakkad', '0491-2505050', 'Palakkad'),
            ('District Collector', 'Collector', 'Revenue — Malappuram', '0483-2760500', 'Malappuram'),
            ('District Collector', 'Collector', 'Revenue — Kozhikode', '0495-2371071', 'Kozhikode'),
            ('District Collector', 'Collector', 'Revenue — Wayanad', '04936-203444', 'Wayanad'),
            ('District Collector', 'Collector', 'Revenue — Kannur', '0497-2700200', 'Kannur'),
            ('District Collector', 'Collector', 'Revenue — Kasaragod', '0499-4255600', 'Kasaragod'),
            ('KSDMA Director', 'Director General', 'State Disaster Management', '0471-2331639', 'Thiruvananthapuram'),
        ]
        for name, desig, dept, phone, district in contacts_data:
            EmergencyContact.objects.create(
                name=name, designation=desig, department=dept,
                phone=phone, district=district, is_active=True
            )
        self.stdout.write(f'✅ Created {len(contacts_data)} emergency contacts')

        self.stdout.write(self.style.SUCCESS('\n🎉 FloodWatch seed data created successfully!'))
        self.stdout.write('👉 Admin login: /admin/ → admin / admin123')
        self.stdout.write('👉 User login: /login/ → user1 / user123')

        # Shelter seed data
        from core.models import EmergencyShelter
        EmergencyShelter.objects.all().delete()
        shelter_data = [
            ('Government HSS Thiruvananthapuram', 'SCHOOL', 'Thiruvananthapuram', 'MG Road, Thiruvananthapuram', 350, 142, 8.4793, 76.9666, 'Rajan K', '9447100001', True, True, True, True, True),
            ('Town Hall Kollam', 'COMMUNITY', 'Kollam', 'Kollam Town Centre', 200, 87, 8.8932, 76.6141, 'Santha M', '9447100002', False, True, True, False, True),
            ('YMCA Hall Pathanamthitta', 'COMMUNITY', 'Pathanamthitta', 'YMCA Road, Pathanamthitta', 180, 180, 9.2648, 76.7870, 'Jose P', '9447100003', True, True, True, True, True),
            ('Govt Model HSS Alappuzha', 'SCHOOL', 'Alappuzha', 'Alappuzha Beach Road', 400, 312, 9.4981, 76.3388, 'Leela N', '9447100004', True, True, True, True, True),
            ('St George College Kottayam', 'SCHOOL', 'Kottayam', 'Aruvithura, Kottayam', 500, 198, 9.5916, 76.5222, 'Thomas V', '9447100005', True, True, True, True, True),
            ('Idukki Civil Station Hall', 'GOVT', 'Idukki', 'Painavu, Idukki', 150, 45, 9.8493, 77.0494, 'Bindhu R', '9447100006', False, True, True, False, True),
            ('Rajagiri College Ernakulam', 'SCHOOL', 'Ernakulam', 'Kalamassery, Ernakulam', 600, 421, 10.0534, 76.3045, 'Anitha S', '9447100007', True, True, True, True, True),
            ('Town Stadium Thrissur', 'STADIUM', 'Thrissur', 'Round East, Thrissur', 800, 356, 10.5276, 76.2144, 'Krishnan N', '9447100008', True, True, True, True, True),
            ('Victoria College Palakkad', 'SCHOOL', 'Palakkad', 'College Road, Palakkad', 450, 449, 10.7867, 76.6548, 'Meena P', '9447100009', False, True, True, False, True),
            ('MES College Malappuram', 'SCHOOL', 'Malappuram', 'Malappuram Town', 300, 112, 11.0510, 76.0711, 'Faisal A', '9447100010', True, True, True, True, True),
            ('Calicut University Hall Kozhikode', 'SCHOOL', 'Kozhikode', 'Thenhipalam, Kozhikode', 500, 0, 11.2588, 75.7804, 'Suresh K', '9447100011', True, True, True, True, True),
            ('Wayanad District Hall', 'GOVT', 'Wayanad', 'Kalpetta, Wayanad', 250, 189, 11.6085, 76.0820, 'Priya T', '9447100012', True, True, True, True, True),
            ('Parassinikadavu Temple Hall Kannur', 'TEMPLE', 'Kannur', 'Parassinikadavu, Kannur', 300, 67, 11.9299, 75.3711, 'Mohan R', '9447100013', False, True, True, False, True),
            ('Kasaragod Govt College', 'SCHOOL', 'Kasaragod', 'Kasaragod Town', 350, 23, 12.4996, 74.9869, 'Rema D', '9447100014', True, True, True, True, True),
        ]
        for name, stype, district, address, cap, occ, lat, lng, contact, phone, med, food, water, power, toilets in shelter_data:
            s = EmergencyShelter(
                name=name, shelter_type=stype, district=district, address=address,
                total_capacity=cap, current_occupancy=occ,
                latitude=lat, longitude=lng,
                contact_person=contact, contact_phone=phone,
                has_medical=med, has_food=food, has_water=water,
                has_power=power, has_toilets=toilets,
            )
            s.save()
        self.stdout.write(f'✅ Created {len(shelter_data)} emergency shelters')

        # Assign rescue teams to shelters
        teams = list(RescueTeam.objects.all()[:6])
        shelters = list(EmergencyShelter.objects.all())
        for i, shelter in enumerate(shelters):
            if teams:
                shelter.assigned_teams.add(teams[i % len(teams)])
        self.stdout.write('✅ Assigned rescue teams to shelters')
