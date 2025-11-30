from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from appointment.models import Service
from homepage.models import City, ServiceCityAvailability


class Command(BaseCommand):
    help = 'Setup cities with strict ordering: Naples/FM First, Others Last.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO(">> STARTING SETUP"))

        # ==========================================
        # 1. SETUP CITIES (With Display Order)
        # ==========================================
        # Format: (Name, Is_Economy, Order)
        cities_config = [
            ('Naples', True, 1),  # First
            ('Fort Myers', True, 2),  # Second
            ('Tampa', False, 3),
            ('Orlando', False, 4),
            ('West Palm Beach', False, 5),
            ('Fort Lauderdale', False, 6),
            ('Others', False, 99),  # Strictly Last
        ]

        city_objects = {}
        for name, is_economy, order in cities_config:
            city, _ = City.objects.update_or_create(
                    name=name,
                    defaults={
                        'is_economy_zone': is_economy,
                        'display_order': order
                    }
            )
            city_objects[name] = city
            print(f"   [CITY] {name} (Order: {order})")

        # ==========================================
        # 2. DEFINE SERVICE GROUPS
        # ==========================================
        # GROUP A: Non-Portrait Services (Weddings, Events, Products)
        ids_non_portrait = [1, 2, 3, 4, 5, 6, 9, 10]

        # GROUP B: Old Legacy Portraits (Hidden from real cities)
        ids_old_portraits = [7, 11, 12, 13]

        # ==========================================
        # 3. LINK "OTHERS" (THE LEGACY VIEW)
        # ==========================================
        print("\n   >> CONFIGURING 'OTHERS' (Linking current DB state)...")
        others_city = city_objects['Others']

        all_legacy_ids = ids_non_portrait + ids_old_portraits
        for svc_id in all_legacy_ids:
            try:
                service = Service.objects.get(id=svc_id)
                ServiceCityAvailability.objects.update_or_create(
                        service=service,
                        city=others_city,
                        defaults={'custom_price': None}
                )
            except Service.DoesNotExist:
                print(f"      [WARNING] Service ID {svc_id} not found.")

        # ==========================================
        # 4. CREATE NEW PORTRAIT PACKAGES
        # ==========================================
        print("\n   >> CREATING NEW PORTRAITS (For Real Cities)...")

        common_desc = (
            "<ul>"
            "<li><strong>Optional Add-ons:</strong> +$70 Studio, +$50 Mini Video</li>"
            "<li><strong>Deposit:</strong> $100 (Non-refundable)</li>"
            "<li><strong>Delivery:</strong> All pictures are DIGITAL (No prints)</li>"
            "</ul>"
        )

        new_portraits_config = [
            {
                'name': 'Portrait - 3 Pictures',
                'price': 150.00,
                'duration': 60,
                'image': 'services/portrait_basic_rDvNdNQ.webp',
                'desc': f"<p>Perfect for a quick update. Naples & Fort Myers ONLY.</p>{common_desc}",
                'economy_only': True
            },
            {
                'name': 'Portrait - 5 Pictures',
                'price': 250.00,
                'duration': 90,
                'image': 'services/portrait_standard.webp',
                'desc': f"<p>Great for capturing multiple angles.</p>{common_desc}",
                'economy_only': False
            },
            {
                'name': 'Portrait - 8 Pictures',
                'price': 350.00,
                'duration': 120,
                'image': 'services/portrait_premium.webp',
                'desc': f"<p>Ideal for comprehensive sessions.</p>{common_desc}",
                'economy_only': False
            },
            {
                'name': 'Portrait - 12 Pictures',
                'price': 450.00,
                'duration': 150,
                'image': 'services/portrait_gold.webp',
                'desc': f"<p>Our most popular package for complete coverage.</p>{common_desc}",
                'economy_only': False
            }
        ]

        new_portrait_services = []
        for conf in new_portraits_config:
            service, _ = Service.objects.update_or_create(
                    name=conf['name'],
                    defaults={
                        'description': conf['desc'],
                        'duration': timedelta(minutes=conf['duration']),
                        'price': conf['price'],
                        'down_payment': 100.00,
                        'currency': 'USD',
                        'image': conf['image'],
                        'allow_rescheduling': False
                    }
            )
            new_portrait_services.append((service, conf['economy_only']))

        # ==========================================
        # 5. LINK REAL CITIES (Naples, Tampa, etc.)
        # ==========================================
        print("\n   >> CONFIGURING REAL CITIES...")
        real_cities = [c for name, c in city_objects.items() if name != 'Others']

        for city in real_cities:
            # A. Link Weddings/Events/Products
            for svc_id in ids_non_portrait:
                try:
                    service = Service.objects.get(id=svc_id)
                    ServiceCityAvailability.objects.update_or_create(
                            service=service,
                            city=city,
                            defaults={'custom_price': None}
                    )
                except Service.DoesNotExist:
                    pass

            # B. Link NEW Portraits (with economy rules)
            for service, economy_only in new_portrait_services:
                if economy_only and not city.is_economy_zone:
                    ServiceCityAvailability.objects.filter(service=service, city=city).delete()
                else:
                    ServiceCityAvailability.objects.update_or_create(
                            service=service,
                            city=city,
                            defaults={'custom_price': None}
                    )

            # C. UNLINK Old Portraits
            for svc_id in ids_old_portraits:
                ServiceCityAvailability.objects.filter(service_id=svc_id, city=city).delete()

        self.stdout.write(self.style.SUCCESS("\n>> DONE. Order set. Others created. Rules applied."))
