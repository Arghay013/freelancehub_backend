from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.marketplace.models import Service
from apps.orders.models import Order

class Command(BaseCommand):
    help = "Seed demo users and services"

    def handle(self, *args, **kwargs):
        # Users
        seller1, _ = User.objects.get_or_create(username="seller1", defaults={"email": "seller1@example.com"})
        if not seller1.check_password("Pass@12345"):
            seller1.set_password("Pass@12345")
        seller1.save()
        seller1.profile.role = "SELLER"
        seller1.profile.is_email_verified = True
        seller1.profile.save()

        buyer1, _ = User.objects.get_or_create(username="buyer1", defaults={"email": "buyer1@example.com"})
        if not buyer1.check_password("Pass@12345"):
            buyer1.set_password("Pass@12345")
        buyer1.save()
        buyer1.profile.role = "BUYER"
        buyer1.profile.is_email_verified = True
        buyer1.profile.save()

        # Services
        Service.objects.filter(seller=seller1).delete()

        services = [
            dict(title="Logo Design for Your Brand", category="graphic", price="25.00", delivery_time_days=2,
                 description="I will design a clean, modern logo with 2 concepts + 3 revisions.",
                 requirements="Brand name, preferred colors, style examples (if any)."),
            dict(title="Resume / CV Writing (ATS Friendly)", category="writing", price="15.00", delivery_time_days=2,
                 description="Professional CV rewrite tailored to your target job and ATS systems.",
                 requirements="Current CV, target job role, key achievements."),
            dict(title="Django REST API Bug Fix & Feature", category="programming", price="40.00", delivery_time_days=3,
                 description="Fix bugs or add a small feature to your Django/DRF project.",
                 requirements="Repo link (optional), error logs, desired feature details."),
            dict(title="YouTube Shorts Video Editing", category="video", price="20.00", delivery_time_days=1,
                 description="High‑energy editing with captions, cuts, and pacing for retention.",
                 requirements="Raw clips, music preference, caption style."),
            dict(title="Facebook Ads Campaign Setup", category="marketing", price="35.00", delivery_time_days=2,
                 description="Campaign setup + audience + creatives suggestions to improve conversions.",
                 requirements="Business page access, product/service details, budget."),
        ]
        created = []
        for s in services:
            created.append(Service.objects.create(seller=seller1, **s))

        # One sample order
        Order.objects.all().delete()
        Order.objects.create(buyer=buyer1, seller=seller1, service=created[0], status=Order.STATUS_COMPLETED, buyer_requirements="Need a minimal logo in blue tones.")

        self.stdout.write(self.style.SUCCESS("✅ Seeded demo data. Users: seller1 / buyer1 (Pass@12345)"))
